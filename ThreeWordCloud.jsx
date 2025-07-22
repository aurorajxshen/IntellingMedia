import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';

function getSpherePositions(n, radius = 2) {
  // Fibonacci sphere for even distribution
  const positions = [];
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < n; i++) {
    const y = 1 - (i / (n - 1)) * 2; // y from 1 to -1
    const radiusAtY = Math.sqrt(1 - y * y);
    const theta = goldenAngle * i;
    const x = Math.cos(theta) * radiusAtY * radius;
    const z = Math.sin(theta) * radiusAtY * radius;
    positions.push([x, y * radius, z]);
  }
  return positions;
}

export default function ThreeWordCloud({ words }) {
  const mountRef = useRef();
  const threeRef = useRef({});

  useEffect(() => {
    if (threeRef.current.renderer) {
      threeRef.current.renderer.dispose && threeRef.current.renderer.dispose();
      mountRef.current.innerHTML = '';
    }
    const width = window.innerWidth;
    const height = window.innerHeight;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 100);
    camera.position.set(0, 0, 8);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    mountRef.current.appendChild(renderer.domElement);

    // Lighting
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const dir = new THREE.DirectionalLight(0xffffff, 0.7);
    dir.position.set(5, 5, 5);
    scene.add(dir);

    // Word sprites
    const n = words.length;
    const positions = getSpherePositions(n, 2.2);
    const group = new THREE.Group();
    for (let i = 0; i < n; i++) {
      const { text, frequency } = words[i];
      const [x, y, z] = positions[i];
      // Create canvas for word
      const canvas = document.createElement('canvas');
      canvas.width = 256;
      canvas.height = 64;
      const ctx = canvas.getContext('2d');
      ctx.font = 'bold 32px Roboto, Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = i === 0 ? '#fff' : '#6cf';
      ctx.globalAlpha = i === 0 ? 1.0 : 0.7;
      ctx.fillText(text, 128, 32);
      const texture = new THREE.CanvasTexture(canvas);
      const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
      const sprite = new THREE.Sprite(material);
      sprite.position.set(x, y, z);
      const scale = i === 0 ? 1.2 : 0.5 + 0.7 * (frequency || 0.5);
      sprite.scale.set(scale, scale * 0.3, 1);
      group.add(sprite);
    }
    scene.add(group);

    // BufferGeometry for drawRange (for demonstration, not strictly needed for sprites)
    const geometry = new THREE.BufferGeometry();
    const flatPositions = positions.flat();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(flatPositions, 3));
    geometry.setDrawRange(0, n); // Show all words

    // Animate
    function animate() {
      group.rotation.y += 0.003;
      renderer.render(scene, camera);
      threeRef.current.frameId = requestAnimationFrame(animate);
    }
    animate();

    // Resize
    function handleResize() {
      const width = window.innerWidth;
      const height = window.innerHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    }
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      cancelAnimationFrame(threeRef.current.frameId);
      window.removeEventListener('resize', handleResize);
      renderer.dispose && renderer.dispose();
      mountRef.current.innerHTML = '';
    };
  }, [words]);

  return <div ref={mountRef} style={{ width: '100vw', height: '100vh' }} />;
} 