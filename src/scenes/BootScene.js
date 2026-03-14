import Phaser from 'phaser';

export class BootScene extends Phaser.Scene {
  constructor() {
    super('Boot');
  }

  preload() {
    // Load minimal assets needed for the preload screen
  }

  create() {
    this.scene.start('Preload');
  }
}
