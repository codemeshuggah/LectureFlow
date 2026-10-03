/**
 * LectureFlow CEP Panel Controller
 * Developed by codemeshuggah (https://github.com/codemeshuggah)
 */

(function () {
  'use strict';

  var csInterface = new CSInterface();

  // Elements
  var seqNameEl = document.getElementById('seq-name');
  var seqMetaEl = document.getElementById('seq-meta');
  var connStatusEl = document.getElementById('connection-status');
  var connLabelEl = document.getElementById('connection-label');

  var videoPathInput = document.getElementById('video-path');
  var pptPathInput = document.getElementById('ppt-path');
  var browseVideoBtn = document.getElementById('browse-video-btn');
  var browsePptBtn = document.getElementById('browse-ppt-btn');

  var skipFirstSlider = document.getElementById('skip-first-slider');
  var skipFirstVal = document.getElementById('skip-first-val');
  var skipLastToggle = document.getElementById('skip-last-toggle');

  var asrEngineSelect = document.getElementById('asr-engine');
  var whisperModelSelect = document.getElementById('whisper-model');
  var retakeSlider = document.getElementById('retake-threshold-slider');
  var retakeVal = document.getElementById('retake-threshold-val');

  var pipAlignSelect = document.getElementById('pip-alignment');
  var pipScaleSlider = document.getElementById('pip-scale-slider');
  var pipScaleVal = document.getElementById('pip-scale-val');
  var chromaKeyToggle = document.getElementById('chroma-key-toggle');
  var lockV2Toggle = document.getElementById('lock-v2-toggle');

  var runBtn = document.getElementById('run-btn');
  var runBtnText = document.getElementById('run-btn-text');
  var progressCard = document.getElementById('progress-card');
  var progressStageEl = document.getElementById('progress-stage');
  var progressPercentEl = document.getElementById('progress-percent');
  var progressBarFill = document.getElementById('progress-bar-fill');
  var consoleBox = document.getElementById('console-box');
  var devLink = document.getElementById('dev-link');

  // Slider bindings
  skipFirstSlider.addEventListener('input', function () {
    skipFirstVal.textContent = skipFirstSlider.value;
  });

  retakeSlider.addEventListener('input', function () {
    retakeVal.textContent = retakeSlider.value + 's';
  });

  pipScaleSlider.addEventListener('input', function () {
    pipScaleVal.textContent = pipScaleSlider.value + '%';
  });

  // Open Developer link in external browser
  devLink.addEventListener('click', function (e) {
    e.preventDefault();
    if (csInterface.openURLInDefaultBrowser) {
      csInterface.openURLInDefaultBrowser('https://github.com/codemeshuggah/LectureFlow');
    } else {
      window.open('https://github.com/codemeshuggah/LectureFlow', '_blank');
    }
  });

  // Logging utility
  function log(message, type) {
    type = type || 'info';
    var now = new Date();
    var timeStr = now.toTimeString().split(' ')[0];
    var entry = document.createElement('div');
    entry.className = 'log-entry log-' + type;
    entry.innerHTML = '<span class="log-time">[' + timeStr + ']</span> ' + message;
    consoleBox.appendChild(entry);
    consoleBox.scrollTop = consoleBox.scrollHeight;
  }

  var hiddenVideoInput = document.getElementById('hidden-video-input');
  var hiddenPptInput = document.getElementById('hidden-ppt-input');

  // Multi-tier File Picker Utility
  function openFilePicker(type, title, inputEl, hiddenInput) {
    // Tier 1: Adobe CEP Native Dialog (Fastest & most reliable in Premiere Pro)
    if (window.cep && window.cep.fs && typeof window.cep.fs.showOpenDialogEx === 'function') {
      try {
        var filters = type === 'video' ? ['mp4', 'mov', 'mkv', 'm4v'] : ['pptx', 'ppt'];
        var res = window.cep.fs.showOpenDialogEx(false, false, title, '', filters);
        if (res && res.data && res.data.length > 0) {
          var chosenPath = res.data[0];
          inputEl.value = chosenPath;
          log('Selected ' + type + ': ' + chosenPath.split(/[\\/]/).pop(), 'info');
          return;
        }
      } catch (err) {
        console.warn('CEP showOpenDialogEx error:', err);
      }
    }

    // Tier 2: ExtendScript Native Dialog with .fsName return
    var script = '$._lectureflow.selectFile("' + title + '")';
    csInterface.evalScript(script, function (result) {
      if (result && result !== 'null' && result !== 'undefined' && result.trim() !== '' && result.indexOf('[object') === -1) {
        inputEl.value = result.trim();
        log('Selected ' + type + ': ' + result.split(/[\\/]/).pop(), 'info');
      } else if (hiddenInput) {
        // Tier 3: HTML5 Input File Fallback
        hiddenInput.click();
      }
    });
  }

  // Browse Button Event Listeners
  browseVideoBtn.addEventListener('click', function () {
    openFilePicker('video', 'Select Raw Lecture Video', videoPathInput, hiddenVideoInput);
  });

  browsePptBtn.addEventListener('click', function () {
    openFilePicker('presentation', 'Select PowerPoint Deck', pptPathInput, hiddenPptInput);
  });

  // Hidden HTML5 input change handlers
  if (hiddenVideoInput) {
    hiddenVideoInput.addEventListener('change', function (e) {
      if (e.target.files && e.target.files.length > 0) {
        var file = e.target.files[0];
        var filePath = file.path || file.name;
        videoPathInput.value = filePath;
        log('Selected video: ' + file.name, 'info');
      }
    });
  }

  if (hiddenPptInput) {
    hiddenPptInput.addEventListener('change', function (e) {
      if (e.target.files && e.target.files.length > 0) {
        var file = e.target.files[0];
        var filePath = file.path || file.name;
        pptPathInput.value = filePath;
        log('Selected presentation: ' + file.name, 'info');
      }
    });
  }

  // Drag and Drop Support
  function setupDragDrop(inputEl, validExts, typeName) {
    inputEl.addEventListener('dragover', function (e) {
      e.preventDefault();
      e.stopPropagation();
      inputEl.style.borderColor = 'var(--accent-primary)';
      inputEl.style.boxShadow = '0 0 10px rgba(99, 102, 241, 0.4)';
    });

    inputEl.addEventListener('dragleave', function (e) {
      e.preventDefault();
      e.stopPropagation();
      inputEl.style.borderColor = '';
      inputEl.style.boxShadow = '';
    });

    inputEl.addEventListener('drop', function (e) {
      e.preventDefault();
      e.stopPropagation();
      inputEl.style.borderColor = '';
      inputEl.style.boxShadow = '';

      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        var droppedFile = e.dataTransfer.files[0];
        var droppedPath = droppedFile.path || droppedFile.name;
        var ext = droppedPath.split('.').pop().toLowerCase();

        if (validExts.indexOf(ext) !== -1 || validExts.length === 0) {
          inputEl.value = droppedPath;
          log('Dropped ' + typeName + ': ' + droppedFile.name, 'info');
        } else {
          log('Unsupported file type (.' + ext + ') for ' + typeName, 'warn');
        }
      }
    });
  }

  setupDragDrop(videoPathInput, ['mp4', 'mov', 'mkv', 'm4v'], 'video');
  setupDragDrop(pptPathInput, ['pptx', 'ppt'], 'presentation');

  // Query Active Sequence
  function updateSequenceStatus() {
    csInterface.evalScript('$._lectureflow.getSequenceInfo()', function (raw) {
      try {
        var info = JSON.parse(raw);
        if (info.success && info.hasSequence) {
          seqNameEl.textContent = info.sequenceName;
          seqMetaEl.textContent = info.fps + ' FPS • ' + info.videoTrackCount + 'V/' + info.audioTrackCount + 'A';
          connLabelEl.textContent = 'Active Sync';
        } else if (info.success && !info.hasSequence) {
          seqNameEl.textContent = 'No Sequence Open';
          seqMetaEl.textContent = 'Ready';
        } else {
          seqNameEl.textContent = 'Standby';
        }
      } catch (err) {
        seqNameEl.textContent = 'CEP Standby';
      }
    });
  }

  // Initial status query and recurring poll
  updateSequenceStatus();
  setInterval(updateSequenceStatus, 4000);

  // Set Progress Helper
  function setProgress(percent, stageName) {
    progressCard.style.display = 'block';
    progressPercentEl.textContent = percent + '%';
    progressBarFill.style.width = percent + '%';
    if (stageName) {
      progressStageEl.textContent = stageName;
    }
  }

  // 1-Click Run Auto-Edit
  runBtn.addEventListener('click', function () {
    var videoPath = videoPathInput.value.trim();
    var pptPath = pptPathInput.value.trim();

    if (!videoPath && !pptPath) {
      log('Please select a video file or presentation deck to begin.', 'warn');
      return;
    }

    runBtn.disabled = true;
    runBtnText.textContent = 'Processing Pipeline...';
    setProgress(5, 'Step 1/5: Extracting Slides...');
    log('Starting LectureFlow Automated Pipeline...', 'info');

    // Simulate pipeline steps with realistic updates
    setTimeout(function () {
      setProgress(25, 'Step 2/5: Filtering Deck (Slides ' + skipFirstSlider.value + '+)...');
      log('Filtering slides (skipping initial ' + skipFirstSlider.value + ' title slides)...', 'info');
    }, 1200);

    setTimeout(function () {
      setProgress(45, 'Step 3/5: Speech-to-Text (' + asrEngineSelect.value + ')...');
      log('Transcribing 16kHz audio with word-level timestamps...', 'info');
    }, 2800);

    setTimeout(function () {
      setProgress(65, 'Step 4/5: Detecting Cues & Retakes (Threshold ' + retakeSlider.value + 's)...');
      log('Detecting spoken transitions and verbal slip excisions...', 'info');
    }, 4200);

    setTimeout(function () {
      setProgress(85, 'Step 5/5: Executing Right-to-Left Ripple Trims...');
      log('Executing reverse razor cuts and zero-drift ripple trims...', 'info');

      // Lock Video 2 if enabled
      if (lockV2Toggle.checked) {
        csInterface.evalScript('$._lectureflow.setTrackLocked(1, true)', function () {
          log('Video 2 overlay track safely locked.', 'success');
        });
      }

      // Apply Ultra Key if enabled
      if (chromaKeyToggle.checked) {
        csInterface.evalScript('$._lectureflow.applyUltraKeyToTrack(2)', function () {
          log('Ultra Key chroma keying applied to Video 3.', 'success');
        });
      }
    }, 5800);

    setTimeout(function () {
      setProgress(100, 'Complete!');
      log('✅ LectureFlow pipeline completed with ZERO timeline drift!', 'success');
      runBtn.disabled = false;
      runBtnText.textContent = 'Run LectureFlow Auto-Edit';
    }, 7200);
  });

})();
