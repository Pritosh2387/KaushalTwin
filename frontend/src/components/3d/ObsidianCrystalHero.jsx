import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

// Fallback component for environments without WebGL
function CrystalFallback({ mousePos }) {
  return (
    <div className="relative w-full h-full flex items-center justify-center pointer-events-none select-none">
      <div className="relative w-72 h-72 sm:w-96 sm:h-96">
        {/* Fine Orbit Ring */}
        <div className="absolute inset-0 rounded-full border border-white/20 -rotate-12 animate-[spin_60s_linear_infinite]" />
        <div className="absolute -inset-4 rounded-full border border-dashed border-white/10 rotate-45 animate-[spin_90s_linear_infinite_reverse]" />
        
        {/* SVG Faceted Obsidian Diamond */}
        <svg
          viewBox="0 0 400 400"
          className="w-full h-full drop-shadow-[0_0_35px_rgba(255,255,255,0.15)] transition-transform duration-500 ease-out"
          style={{
            transform: `translate(${mousePos.x * 15}px, ${mousePos.y * 15}px) rotate(${mousePos.x * 8}deg)`,
          }}
        >
          <defs>
            <linearGradient id="facet1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#252528" />
              <stop offset="100%" stopColor="#050505" />
            </linearGradient>
            <linearGradient id="facet2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#1a1a1c" />
              <stop offset="100%" stopColor="#020202" />
            </linearGradient>
            <linearGradient id="facet3" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#2e2e32" />
              <stop offset="50%" stopColor="#121214" />
              <stop offset="100%" stopColor="#050505" />
            </linearGradient>
            <linearGradient id="facetEdge" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(255,255,255,0.8)" />
              <stop offset="100%" stopColor="rgba(255,255,255,0.1)" />
            </linearGradient>
          </defs>

          {/* Facets */}
          <polygon points="200,40 280,130 200,160 120,130" fill="url(#facet1)" stroke="rgba(255,255,255,0.4)" strokeWidth="0.8" />
          <polygon points="280,130 360,180 280,240 200,160" fill="url(#facet2)" stroke="rgba(255,255,255,0.3)" strokeWidth="0.8" />
          <polygon points="120,130 200,160 120,240 40,180" fill="url(#facet3)" stroke="rgba(255,255,255,0.3)" strokeWidth="0.8" />
          <polygon points="200,160 280,240 200,360 120,240" fill="url(#facet1)" stroke="rgba(255,255,255,0.5)" strokeWidth="1" />
          <polygon points="280,240 360,180 320,290 200,360" fill="url(#facet2)" stroke="rgba(255,255,255,0.2)" strokeWidth="0.8" />
          <polygon points="120,240 200,360 80,290 40,180" fill="url(#facet3)" stroke="rgba(255,255,255,0.2)" strokeWidth="0.8" />
          
          {/* Specular Edge Highlights */}
          <line x1="200" y1="40" x2="280" y2="130" stroke="url(#facetEdge)" strokeWidth="1.5" />
          <line x1="200" y1="160" x2="200" y2="360" stroke="rgba(255,255,255,0.9)" strokeWidth="1.2" />
          <line x1="120" y1="130" x2="200" y2="160" stroke="rgba(255,255,255,0.6)" strokeWidth="1" />
        </svg>

        {/* Floating Shards */}
        <div className="absolute top-10 right-4 w-4 h-6 border border-white/40 bg-zinc-900 rotate-45 transform skew-x-12 animate-pulse" />
        <div className="absolute bottom-16 left-6 w-3 h-5 border border-white/30 bg-zinc-950 -rotate-12 animate-bounce" />
      </div>
    </div>
  );
}

export function ObsidianCrystalHero({ onCrystalHover }) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const [hasWebGL, setHasWebGL] = useState(true);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check WebGL availability
    const testCanvas = document.createElement('canvas');
    const gl = testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl');
    if (!gl) {
      setHasWebGL(false);
      return;
    }

    let width = container.clientWidth || window.innerWidth * 0.45;
    let height = container.clientHeight || window.innerHeight;

    // Three.js Scene Setup
    const scene = new THREE.Scene();
    scene.background = null; // transparent to allow deep #000000 background

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(0, 0, 7.5);

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas: canvasRef.current,
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance',
      });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.2;
    } catch {
      setHasWebGL(false);
      return;
    }

    // Custom Faceted Polyhedron for Realistic Black Diamond Silhouette
    // Asymmetric, angular, planar faceted diamond
    const vertices = [
      // Top apex
      0, 2.3, 0,
      // Crown upper ring (irregular facets)
      -1.0, 1.2, 0.9,
      1.1, 1.3, 0.8,
      1.2, 1.1, -0.9,
      -0.9, 1.4, -1.0,
      // Girdle (widest perimeter with sharp angular facets)
      -1.9, 0.1, 1.4,
      0.2, 0.3, 2.0,
      1.8, -0.1, 1.2,
      2.1, 0.2, -0.8,
      0.0, -0.2, -2.1,
      -1.8, 0.2, -1.2,
      // Lower pavilion ring
      -1.1, -1.3, 0.9,
      1.0, -1.4, 0.7,
      1.1, -1.2, -0.9,
      -1.0, -1.3, -1.0,
      // Bottom culet point
      0, -2.4, 0,
    ];

    const indices = [
      // Top Crown Facets
      0, 1, 2,
      0, 2, 3,
      0, 3, 4,
      0, 4, 1,
      // Crown to Girdle
      1, 5, 6,
      1, 6, 2,
      2, 6, 7,
      2, 7, 8,
      2, 8, 3,
      3, 8, 9,
      3, 9, 4,
      4, 9, 10,
      4, 10, 5,
      4, 5, 1,
      // Girdle to Pavilion
      5, 11, 6,
      6, 11, 12,
      6, 12, 7,
      7, 12, 13,
      7, 13, 8,
      8, 13, 9,
      9, 13, 14,
      9, 14, 10,
      10, 14, 5,
      5, 14, 11,
      // Pavilion to Culet
      11, 15, 12,
      12, 15, 13,
      13, 15, 14,
      14, 15, 11,
    ];

    const crystalGeometry = new THREE.PolyhedronGeometry(vertices, indices, 2.2, 0);
    crystalGeometry.computeVertexNormals();

    // Material: Polished Obsidian Black Diamond
    const obsidianMaterial = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color(0x060608),
      emissive: new THREE.Color(0x010102),
      roughness: 0.11,
      metalness: 0.25,
      clearcoat: 1.0,
      clearcoatRoughness: 0.05,
      reflectivity: 0.98,
      transmission: 0.2,
      ior: 2.417,
      thickness: 1.8,
      flatShading: true, // Crucial for crisp planar facets!
      specularIntensity: 1.0,
      specularColor: new THREE.Color(0xffffff),
    });

    const crystalMesh = new THREE.Mesh(crystalGeometry, obsidianMaterial);
    scene.add(crystalMesh);

    // Razor-Sharp White Wireframe Edges
    const edgesGeometry = new THREE.EdgesGeometry(crystalGeometry, 18);
    const edgesMaterial = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.45,
      linewidth: 1,
    });
    const edgesMesh = new THREE.LineSegments(edgesGeometry, edgesMaterial);
    crystalMesh.add(edgesMesh);

    // Orbit Ring 1 (Thin, delicate luxury orbit line)
    const orbitCurve1 = new THREE.EllipseCurve(0, 0, 3.4, 2.1, 0, 2 * Math.PI, false, 0);
    const orbitPoints1 = orbitCurve1.getPoints(120);
    const orbitGeometry1 = new THREE.BufferGeometry().setFromPoints(
      orbitPoints1.map(p => new THREE.Vector3(p.x, 0, p.y))
    );
    const orbitMaterial1 = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.18,
    });
    const orbitLine1 = new THREE.LineLoop(orbitGeometry1, orbitMaterial1);
    orbitLine1.rotation.x = Math.PI / 3.2;
    orbitLine1.rotation.y = Math.PI / 6;
    scene.add(orbitLine1);

    // Orbit Ring 2 (Secondary counter-tilted orbit)
    const orbitCurve2 = new THREE.EllipseCurve(0, 0, 4.0, 2.6, 0, 2 * Math.PI, false, 0);
    const orbitPoints2 = orbitCurve2.getPoints(120);
    const orbitGeometry2 = new THREE.BufferGeometry().setFromPoints(
      orbitPoints2.map(p => new THREE.Vector3(p.x, p.y, 0))
    );
    const orbitMaterial2 = new THREE.LineBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.09,
    });
    const orbitLine2 = new THREE.LineLoop(orbitGeometry2, orbitMaterial2);
    orbitLine2.rotation.x = -Math.PI / 4;
    orbitLine2.rotation.z = Math.PI / 5;
    scene.add(orbitLine2);

    // Floating Crystal Fragments (3-4 smaller shards tumbling in surrounding darkness)
    const fragments = [];
    const shardPositions = [
      { pos: [2.5, 1.8, -0.8], scale: 0.28, rotSpeed: [0.008, 0.012, 0.005] },
      { pos: [-2.2, -1.9, 0.5], scale: 0.22, rotSpeed: [-0.01, 0.007, -0.009] },
      { pos: [2.0, -2.1, -0.5], scale: 0.25, rotSpeed: [0.006, -0.01, 0.008] },
      { pos: [-2.6, 1.6, -1.0], scale: 0.18, rotSpeed: [-0.007, -0.008, 0.011] },
    ];

    const shardGeometry = new THREE.OctahedronGeometry(1, 0);
    shardPositions.forEach((cfg) => {
      const shardMesh = new THREE.Mesh(shardGeometry, obsidianMaterial);
      shardMesh.position.set(...cfg.pos);
      shardMesh.scale.setScalar(cfg.scale);

      const shardEdges = new THREE.LineSegments(
        new THREE.EdgesGeometry(shardGeometry),
        new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35 })
      );
      shardMesh.add(shardEdges);

      scene.add(shardMesh);
      fragments.push({ mesh: shardMesh, ...cfg, baseY: cfg.pos[1] });
    });

    // Sparse White Particle Field (Understated ambient dust in darkness)
    const particleCount = 70;
    const particleGeometry = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePositions[i] = (Math.random() - 0.5) * 12;
      particlePositions[i + 1] = (Math.random() - 0.5) * 10;
      particlePositions[i + 2] = (Math.random() - 0.5) * 8;
    }
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    const particleMaterial = new THREE.PointsMaterial({
      color: 0xffffff,
      size: 0.035,
      transparent: true,
      opacity: 0.35,
    });
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    // Controlled Cinematic Lighting Setup
    // 1. Very dim ambient light so shadows stay deep black
    const ambientLight = new THREE.AmbientLight(0x050505, 0.8);
    scene.add(ambientLight);

    // 2. Razor-Sharp White Key Rim Light (Casts brilliant white highlights)
    const rimLight1 = new THREE.DirectionalLight(0xffffff, 4.2);
    rimLight1.position.set(-5, 6, 4);
    scene.add(rimLight1);

    // 3. Opposing Silver Rim Light (defines silhouette from behind)
    const rimLight2 = new THREE.DirectionalLight(0xe4e4e7, 3.5);
    rimLight2.position.set(6, -4, -4);
    scene.add(rimLight2);

    // 4. Razor Top-Down Light
    const topLight = new THREE.DirectionalLight(0xffffff, 2.2);
    topLight.position.set(0, 8, 2);
    scene.add(topLight);

    // 5. Interactive Mouse Light (Follows cursor to make facets gleam dynamically)
    const mouseLight = new THREE.PointLight(0xffffff, 2.5, 12);
    mouseLight.position.set(0, 0, 5);
    scene.add(mouseLight);

    // Interaction State
    let targetRotX = 0;
    let targetRotY = 0;
    let currentRotX = 0;
    let currentRotY = 0;
    let targetCamX = 0;
    let targetCamY = 0;

    const handleMouseMove = (e) => {
      const rect = container.getBoundingClientRect();
      const normX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const normY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      setMousePos({ x: normX, y: normY });

      targetRotY = normX * 0.45;
      targetRotX = -normY * 0.35;
      targetCamX = normX * 0.4;
      targetCamY = normY * 0.3;

      mouseLight.position.x = normX * 4;
      mouseLight.position.y = normY * 4;
    };

    window.addEventListener('mousemove', handleMouseMove);

    // Handle Resize
    const handleResize = () => {
      if (!container) return;
      width = container.clientWidth || window.innerWidth * 0.45;
      height = container.clientHeight || window.innerHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };

    window.addEventListener('resize', handleResize);

    // Animation Loop
    let animationFrameId;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Idle multi-axis continuous rotation
      crystalMesh.rotation.y += 0.0035;
      crystalMesh.rotation.x = Math.sin(elapsedTime * 0.3) * 0.12 + currentRotX;
      crystalMesh.rotation.z = Math.cos(elapsedTime * 0.2) * 0.08;

      // Gentle vertical floating
      crystalMesh.position.y = Math.sin(elapsedTime * 0.7) * 0.15;

      // Smooth mouse parallax damping
      currentRotX += (targetRotX - currentRotX) * 0.05;
      currentRotY += (targetRotY - currentRotY) * 0.05;
      crystalMesh.rotation.y += currentRotY * 0.02;

      camera.position.x += (targetCamX - camera.position.x) * 0.04;
      camera.position.y += (targetCamY - camera.position.y) * 0.04;
      camera.lookAt(0, 0, 0);

      // Animate orbit rings
      orbitLine1.rotation.z += 0.0015;
      orbitLine2.rotation.y -= 0.001;

      // Animate floating crystal shards
      fragments.forEach((item, idx) => {
        item.mesh.rotation.x += item.rotSpeed[0];
        item.mesh.rotation.y += item.rotSpeed[1];
        item.mesh.rotation.z += item.rotSpeed[2];
        item.mesh.position.y = item.baseY + Math.sin(elapsedTime * 0.9 + idx) * 0.18;
      });

      // Slowly rotate particle field
      particles.rotation.y += 0.0004;

      renderer.render(scene, camera);
    };

    animate();

    // Cleanup resources properly
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);

      crystalGeometry.dispose();
      obsidianMaterial.dispose();
      edgesGeometry.dispose();
      edgesMaterial.dispose();
      orbitGeometry1.dispose();
      orbitMaterial1.dispose();
      orbitGeometry2.dispose();
      orbitMaterial2.dispose();
      shardGeometry.dispose();
      particleGeometry.dispose();
      particleMaterial.dispose();
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full min-h-[460px] lg:min-h-[640px] flex items-center justify-center select-none"
      onMouseEnter={() => onCrystalHover && onCrystalHover(true)}
      onMouseLeave={() => onCrystalHover && onCrystalHover(false)}
    >
      {hasWebGL ? (
        <canvas ref={canvasRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
      ) : (
        <CrystalFallback mousePos={mousePos} />
      )}

      {/* Subtle modern status indicator */}
      <div className="absolute bottom-6 right-6 hidden sm:flex items-center gap-2 text-xs text-zinc-400 bg-black/70 backdrop-blur-md px-3.5 py-1.5 border border-white/10 pointer-events-none">
        <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
        <span className="font-sans text-[11px] text-zinc-300">Interactive 3D Skill Visualization</span>
      </div>
    </div>
  );
}

export default ObsidianCrystalHero;
