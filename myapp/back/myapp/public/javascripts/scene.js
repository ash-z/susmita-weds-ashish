import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

var container = document.getElementById('scene');

var scene = new THREE.Scene();
scene.background = new THREE.Color(0x11151c);

var camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 100);
camera.position.set(2, 2, 4);

var renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

var controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

var cube = new THREE.Mesh(
  new THREE.BoxGeometry(1.5, 1.5, 1.5),
  new THREE.MeshStandardMaterial({ color: 0x00b7ff })
);
scene.add(cube);

scene.add(new THREE.AmbientLight(0xffffff, 0.6));
var light = new THREE.DirectionalLight(0xffffff, 2);
light.position.set(3, 5, 2);
scene.add(light);

window.addEventListener('resize', function() {
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
});

renderer.setAnimationLoop(function() {
  cube.rotation.x += 0.005;
  cube.rotation.y += 0.01;
  controls.update();
  renderer.render(scene, camera);
});
