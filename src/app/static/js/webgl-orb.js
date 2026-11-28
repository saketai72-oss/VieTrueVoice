/**
 * ViTrueVoice v0.9.4 — WebGL 3D Liquid Obsidian Orb (Three.js r125)
 * Simplex 3D Noise + Fresnel Rim GLSL Shader (Stitch ANIMATION_12 fidelity).
 *
 * Public API on window.vieTrueVoice3D:
 *   - setStateColor(hex): smooth THREE.Color.lerp rim/accent color transition
 *   - setRimColor(hex):   alias of setStateColor(hex)
 *   - setAudioLevel(val): live audio energy reactivity [0..1]
 *   - setScanIntensity(v): forensic scanning sweep intensity [0..1]
 *   - setEnabled(bool):   cleanly pauses/resumes RAF & toggles fallback grid
 *   - isEnabled():        returns current WebGL active state
 *   - dispose():          frees GPU resources
 */
(function () {
  'use strict';

  const VERTEX_SHADER = /* glsl */ `
    uniform float uTime;
    uniform float uAudioLevel;
    uniform float uScanIntensity;
    varying vec3 vNormal;
    varying vec3 vWorldPosition;
    varying vec3 vViewPosition;
    varying float vDisplacement;

    // 3D Simplex Noise — Ashima Arts / Stefan Gustavson
    vec4 permute(vec4 x) { return mod(((x * 34.0) + 1.0) * x, 289.0); }
    vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

    float snoise(vec3 v) {
      const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0);
      const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);

      vec3 i  = floor(v + dot(v, C.yyy));
      vec3 x0 = v - i + dot(i, C.xxx);

      vec3 g = step(x0.yzx, x0.xyz);
      vec3 l = 1.0 - g;
      vec3 i1 = min(g.xyz, l.zxy);
      vec3 i2 = max(g.xyz, l.zxy);

      vec3 x1 = x0 - i1 + C.xxx;
      vec3 x2 = x0 - i2 + C.yyy;
      vec3 x3 = x0 - D.yyy;

      i = mod(i, 289.0);
      vec4 p = permute(permute(permute(
                i.z + vec4(0.0, i1.z, i2.z, 1.0))
              + i.y + vec4(0.0, i1.y, i2.y, 1.0))
              + i.x + vec4(0.0, i1.x, i2.x, 1.0));

      float n_ = 1.0 / 7.0;
      vec3 ns = n_ * D.wyz - D.xzx;

      vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
      vec4 x_ = floor(j * ns.z);
      vec4 y_ = floor(j - 7.0 * x_);

      vec4 x = x_ * ns.x + ns.yyyy;
      vec4 y = y_ * ns.x + ns.yyyy;
      vec4 h = 1.0 - abs(x) - abs(y);

      vec4 b0 = vec4(x.xy, y.xy);
      vec4 b1 = vec4(x.zw, y.zw);

      vec4 s0 = floor(b0) * 2.0 + 1.0;
      vec4 s1 = floor(b1) * 2.0 + 1.0;
      vec4 sh = -step(h, vec4(0.0));

      vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
      vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;

      vec3 p0 = vec3(a0.xy, h.x);
      vec3 p1 = vec3(a0.zw, h.y);
      vec3 p2 = vec3(a1.xy, h.z);
      vec3 p3 = vec3(a1.zw, h.w);

      vec4 norm = taylorInvSqrt(vec4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)));
      p0 *= norm.x;
      p1 *= norm.y;
      p2 *= norm.z;
      p3 *= norm.w;

      vec4 m = max(0.6 - vec4(dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), 0.0);
      m = m * m;
      return 42.0 * dot(m * m, vec4(dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)));
    }

    void main() {
      float speed = 0.28 + uScanIntensity * 0.55 + uAudioLevel * 0.45;
      float freq = 1.45 + uScanIntensity * 0.85;
      float n1 = snoise(normal * freq + vec3(uTime * speed, -uTime * speed * 0.7, uTime * 0.18));
      float n2 = snoise(normal * (freq * 2.2) - vec3(uTime * 0.35, uTime * 0.25, -uTime * 0.4)) * 0.35;

      float amp = 0.16 + uAudioLevel * 0.34 + uScanIntensity * 0.14;
      float disp = (n1 + n2) * amp;
      vDisplacement = disp;

      vec3 displaced = position + normal * disp;
      vec4 worldPos = modelMatrix * vec4(displaced, 1.0);
      vWorldPosition = worldPos.xyz;

      vec4 mvPosition = viewMatrix * worldPos;
      vViewPosition = -mvPosition.xyz;
      vNormal = normalize(normalMatrix * normal);

      gl_Position = projectionMatrix * mvPosition;
    }
  `;

  const FRAGMENT_SHADER = /* glsl */ `
    uniform float uTime;
    uniform vec3 uRimColor;
    uniform float uAudioLevel;
    uniform float uScanIntensity;
    varying vec3 vNormal;
    varying vec3 vWorldPosition;
    varying vec3 vViewPosition;
    varying float vDisplacement;

    void main() {
      vec3 normal = normalize(vNormal);
      vec3 viewDir = normalize(vViewPosition);

      // Liquid obsidian core with subtle iridescent specular sheen
      float ndotv = clamp(dot(normal, viewDir), 0.0, 1.0);
      float fresnel = pow(1.0 - ndotv, 2.75);

      vec3 obsidianCore = vec3(0.035, 0.036, 0.044);
      vec3 obsidianMid  = vec3(0.085, 0.088, 0.102);

      // Ridge highlight along displaced acoustic crests
      float crest = smoothstep(-0.06, 0.28, vDisplacement);
      vec3 baseColor = mix(obsidianCore, obsidianMid, crest * 0.85);

      // Studio rim lighting & directional cold key reflection
      vec3 keyLightDir = normalize(vec3(0.65, 0.8, 0.55));
      vec3 halfVec = normalize(keyLightDir + viewDir);
      float spec = pow(max(dot(normal, halfVec), 0.0), 42.0) * 0.32;

      // Forensic scan band traveling vertically along world Y
      float scanWave = sin(vWorldPosition.y * 12.0 - uTime * 7.5) * 0.5 + 0.5;
      float scanLine = smoothstep(0.84, 0.99, scanWave) * (0.14 + uScanIntensity * 0.65);

      float rimStrength = (0.78 + uAudioLevel * 0.85 + uScanIntensity * 0.45);
      vec3 rimGlow = uRimColor * fresnel * rimStrength;
      vec3 innerPulse = uRimColor * crest * (0.07 + uAudioLevel * 0.24);
      vec3 scanGlow = uRimColor * scanLine * (0.45 + fresnel * 0.7);

      vec3 finalColor = baseColor + vec3(spec) * (0.55 + uRimColor * 0.45) + rimGlow + innerPulse + scanGlow;

      gl_FragColor = vec4(finalColor, 1.0);
    }
  `;

  function createNoopController(fallbackEl, canvasEl) {
    let enabled = false;
    if (canvasEl) canvasEl.classList.add('is-disabled');
    if (fallbackEl) fallbackEl.classList.add('is-active');
    return {
      setStateColor: function () {},
      setRimColor: function () {},
      setAudioLevel: function () {},
      setScanIntensity: function () {},
      setEnabled: function () { return false; },
      isEnabled: function () { return enabled; },
      dispose: function () {},
    };
  }

  function initWebGLOrb() {
    const canvas = document.getElementById('vtv-webgl-canvas');
    const fallbackEl = document.getElementById('vtv-obsidian-fallback');

    if (!canvas || typeof window.THREE === 'undefined') {
      window.vieTrueVoice3D = createNoopController(fallbackEl, canvas);
      return;
    }

    const THREE = window.THREE;
    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance',
      });
    } catch (_err) {
      window.vieTrueVoice3D = createNoopController(fallbackEl, canvas);
      return;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    camera.position.set(0, 0, 5.1);

    const currentRimColor = new THREE.Color('#00e599');
    const targetRimColor = new THREE.Color('#00e599');

    const uniforms = {
      uTime: { value: 0 },
      uRimColor: { value: currentRimColor },
      uAudioLevel: { value: 0 },
      uScanIntensity: { value: 0 },
    };

    // High-resolution obsidian orb
    const orbGeo = new THREE.IcosahedronGeometry(1.52, 64);
    const orbMat = new THREE.ShaderMaterial({
      vertexShader: VERTEX_SHADER,
      fragmentShader: FRAGMENT_SHADER,
      uniforms: uniforms,
      transparent: false,
    });
    const orbMesh = new THREE.Mesh(orbGeo, orbMat);
    scene.add(orbMesh);

    // Subtle geometric orbital telemetry rings around the obsidian sphere
    const ringGeo = new THREE.RingGeometry(2.08, 2.092, 128);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x6dffba,
      transparent: true,
      opacity: 0.16,
      side: THREE.DoubleSide,
    });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI * 0.38;
    ringMesh.rotation.y = -Math.PI * 0.12;
    scene.add(ringMesh);

    // Sparse acoustic dust particles
    const particleCount = 140;
    const pPositions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const r = 2.35 + Math.random() * 2.4;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      pPositions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pPositions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pPositions[i * 3 + 2] = r * Math.cos(phi);
    }
    const pGeo = new THREE.BufferGeometry();
    pGeo.setAttribute('position', new THREE.BufferAttribute(pPositions, 3));
    const pMat = new THREE.PointsMaterial({
      color: 0xbacbbe,
      size: 0.022,
      transparent: true,
      opacity: 0.35,
    });
    const particles = new THREE.Points(pGeo, pMat);
    scene.add(particles);

    let enabled = true;
    let rafId = null;
    let lastTime = performance.now();
    let targetAudioLevel = 0;
    let currentAudioLevel = 0;
    let targetScanIntensity = 0;
    let currentScanIntensity = 0;

    const pointer = { x: 0, y: 0, tx: 0, ty: 0 };

    function resize() {
      const parent = canvas.parentElement || document.documentElement;
      const w = Math.max(parent.clientWidth, 1);
      const h = Math.max(parent.clientHeight, 1);
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      renderer.setPixelRatio(dpr);
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      // Gently adjust distance on narrow mobile viewports so orb frames nicely
      camera.position.z = w < 640 ? 6.1 : 5.05;
      camera.updateProjectionMatrix();
    }

    resize();
    window.addEventListener('resize', resize, { passive: true });

    window.addEventListener(
      'pointermove',
      function (ev) {
        pointer.tx = (ev.clientX / Math.max(window.innerWidth, 1) - 0.5) * 2;
        pointer.ty = (ev.clientY / Math.max(window.innerHeight, 1) - 0.5) * 2;
      },
      { passive: true }
    );

    function animate(now) {
      if (!enabled) {
        rafId = null;
        return;
      }
      rafId = window.requestAnimationFrame(animate);

      const dt = Math.min((now - lastTime) / 1000, 0.05);
      lastTime = now;

      uniforms.uTime.value += dt;

      // Smoothly interpolate rim/state color, audio reactivity, and scan intensity
      currentRimColor.lerp(targetRimColor, Math.min(1, dt * 4.5));
      ringMat.color.copy(currentRimColor);

      currentAudioLevel += (targetAudioLevel - currentAudioLevel) * Math.min(1, dt * 10);
      targetAudioLevel *= Math.pow(0.08, dt); // Natural smooth decay when idle
      uniforms.uAudioLevel.value = currentAudioLevel;

      currentScanIntensity += (targetScanIntensity - currentScanIntensity) * Math.min(1, dt * 5);
      uniforms.uScanIntensity.value = currentScanIntensity;

      pointer.x += (pointer.tx - pointer.x) * Math.min(1, dt * 3.5);
      pointer.y += (pointer.ty - pointer.y) * Math.min(1, dt * 3.5);

      orbMesh.rotation.y += dt * (0.14 + currentScanIntensity * 0.45);
      orbMesh.rotation.x = pointer.y * 0.22 + Math.sin(uniforms.uTime.value * 0.35) * 0.08;
      orbMesh.rotation.z = -pointer.x * 0.14;

      const scalePulse = 1 + currentAudioLevel * 0.075;
      orbMesh.scale.setScalar(scalePulse);

      ringMesh.rotation.z += dt * (0.18 + currentScanIntensity * 0.6);
      ringMesh.rotation.x = Math.PI * 0.38 + pointer.y * 0.16;
      ringMat.opacity = 0.14 + currentAudioLevel * 0.28 + currentScanIntensity * 0.22;

      particles.rotation.y -= dt * 0.035;
      particles.rotation.x = pointer.y * 0.08;

      renderer.render(scene, camera);
    }

    function setStateColor(hex) {
      if (!hex) return;
      try {
        targetRimColor.set(hex);
      } catch (_err) {
        // Ignore invalid CSS color strings safely
      }
    }

    function setAudioLevel(val) {
      const n = Number(val);
      if (Number.isFinite(n)) {
        targetAudioLevel = Math.max(0, Math.min(1.5, n));
      }
    }

    function setScanIntensity(val) {
      const n = Number(val);
      if (Number.isFinite(n)) {
        targetScanIntensity = Math.max(0, Math.min(1.2, n));
      }
    }

    function setEnabled(nextState) {
      const next = Boolean(nextState);
      if (next === enabled) return enabled;
      enabled = next;

      if (enabled) {
        canvas.classList.remove('is-disabled');
        if (fallbackEl) fallbackEl.classList.remove('is-active');
        lastTime = performance.now();
        if (rafId === null) {
          rafId = window.requestAnimationFrame(animate);
        }
      } else {
        if (rafId !== null) {
          window.cancelAnimationFrame(rafId);
          rafId = null;
        }
        canvas.classList.add('is-disabled');
        if (fallbackEl) fallbackEl.classList.add('is-active');
      }
      return enabled;
    }

    function dispose() {
      setEnabled(false);
      window.removeEventListener('resize', resize);
      orbGeo.dispose();
      orbMat.dispose();
      ringGeo.dispose();
      ringMat.dispose();
      pGeo.dispose();
      pMat.dispose();
      renderer.dispose();
    }

    // Pause cleanly if browser tab goes hidden to save GPU cycles
    document.addEventListener('visibilitychange', function () {
      if (!enabled) return;
      if (document.hidden) {
        if (rafId !== null) {
          window.cancelAnimationFrame(rafId);
          rafId = null;
        }
      } else if (rafId === null) {
        lastTime = performance.now();
        rafId = window.requestAnimationFrame(animate);
      }
    });

    // Respect prefers-reduced-motion only by slowing initial boot gently, keep 3D on unless toggled
    rafId = window.requestAnimationFrame(animate);

    window.vieTrueVoice3D = {
      setStateColor: setStateColor,
      setRimColor: setStateColor, // Explicit alias fixing Stitch template bug
      setAudioLevel: setAudioLevel,
      setScanIntensity: setScanIntensity,
      setEnabled: setEnabled,
      isEnabled: function () { return enabled; },
      dispose: dispose,
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWebGLOrb);
  } else {
    initWebGLOrb();
  }
})();
