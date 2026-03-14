import Phaser from 'phaser';

export class GameScene extends Phaser.Scene {
  constructor() {
    super('Game');
  }

  create() {
    this.add.text(400, 300, 'GalacticX', {
      fontSize: '32px',
      fontFamily: 'monospace',
      color: '#FFE81F'
    }).setOrigin(0.5);
  }

  update() {
    // Game loop
  }
}
