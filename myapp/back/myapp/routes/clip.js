var express = require('express');
var fs = require('fs');
var os = require('os');
var path = require('path');
var crypto = require('crypto');
var execFile = require('child_process').execFile;
var ffmpegPath = require('ffmpeg-static');
var router = express.Router();

/* GET song clip maker. */
router.get('/', function(req, res, next) {
  res.render('clip', { title: 'Song Clip Maker' });
});

/*
 * POST /clip/convert: the browser sends a file it could not decode itself
 * (WMA, AMR, APE, AC3, video files...) and gets back a WAV it can read.
 */
var MAX_UPLOAD = 500 * 1024 * 1024;

router.post('/convert', function(req, res, next) {
  var base = path.join(os.tmpdir(), 'clip-' + crypto.randomBytes(8).toString('hex'));
  var input = base + '.in';
  var output = base + '.wav';
  var received = 0;
  var tooBig = false;
  function cleanup() {
    fs.unlink(input, function() {});
    fs.unlink(output, function() {});
  }

  var file = fs.createWriteStream(input);
  req.on('data', function(chunk) {
    received += chunk.length;
    if (received > MAX_UPLOAD && !tooBig) {
      tooBig = true;
      req.unpipe(file);
      file.end();
      cleanup();
      res.status(413).send('That file is too big. The limit is 500 MB.');
    }
  });
  req.pipe(file);
  file.on('error', function(err) { cleanup(); next(err); });
  file.on('finish', function() {
    if (tooBig) return;
    if (!received) {
      cleanup();
      return res.status(400).send('No file received.');
    }
    var args = ['-hide_banner', '-loglevel', 'error', '-y', '-i', input,
      '-vn', '-ac', '2', '-ar', '44100', '-c:a', 'pcm_s16le', output];
    execFile(ffmpegPath, args, { timeout: 5 * 60 * 1000 }, function(err) {
      if (err) {
        cleanup();
        return res.status(415).send('That file has no audio we can read.');
      }
      res.type('audio/wav').sendFile(output, cleanup);
    });
  });
});

module.exports = router;
