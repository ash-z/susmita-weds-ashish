var express = require('express');
var router = express.Router();

/* GET song clip maker. */
router.get('/', function(req, res, next) {
  res.render('clip', { title: 'Song Clip Maker' });
});

module.exports = router;
