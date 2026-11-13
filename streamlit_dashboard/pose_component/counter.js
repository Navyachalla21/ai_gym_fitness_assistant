/* Rep counter for bicep curls: pure logic, no camera code (so it can be tested). */
(function (root) {
  const CURL = 60, EXTEND = 150, CONFIRM = 2, DRIFT = 0.30;

  function angle(a, b, c) {           // angle at b, points are {x,y} in pixels
    const v1 = { x: a.x - b.x, y: a.y - b.y }, v2 = { x: c.x - b.x, y: c.y - b.y };
    const dot = v1.x * v2.x + v1.y * v2.y;
    const n = Math.hypot(v1.x, v1.y) * Math.hypot(v2.x, v2.y);
    if (!n) return 180;
    return Math.acos(Math.max(-1, Math.min(1, dot / n))) * 180 / Math.PI;
  }

  function Counter() { this.reset(); }
  Counter.prototype.reset = function () {
    this.reps = 0; this.good = 0; this.stage = null;   // stage: 'down' (arm straight) or 'up' (curled)
    this.upFrames = 0; this.downFrames = 0; this.driftThisRep = false;
  };
  /* update(angleDeg, drifting) -> list of events: 'down', 'rep', 'drift' */
  Counter.prototype.update = function (ang, drifting) {
    const ev = [];
    if (drifting && this.stage === 'down') { /* elbow swinging while lifting */ }
    if (drifting && !this.driftThisRep) { this.driftThisRep = true; ev.push('drift'); }
    if (ang > EXTEND) {
      this.downFrames++; this.upFrames = 0;
      if (this.downFrames >= CONFIRM && this.stage !== 'down') {
        this.stage = 'down'; this.driftThisRep = false; ev.push('down');
      }
    } else if (ang < CURL) {
      this.upFrames++; this.downFrames = 0;
      if (this.upFrames >= CONFIRM && this.stage === 'down') {
        this.stage = 'up'; this.reps++;
        if (!this.driftThisRep) this.good++;
        ev.push('rep');
      }
    } else { this.upFrames = 0; this.downFrames = 0; }
    return ev;
  };
  root.PoseCounter = { Counter, angle, CURL, EXTEND, DRIFT };
  if (typeof module !== 'undefined') module.exports = root.PoseCounter;
})(typeof window !== 'undefined' ? window : globalThis);
