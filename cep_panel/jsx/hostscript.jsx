/**
 * LectureFlow ExtendScript Host Script
 * Developed by codemeshuggah (https://github.com/codemeshuggah)
 */

if (typeof $ === "undefined") {
    $ = {};
}

$._lectureflow = {
    // 1. Get Active Project & Sequence Status
    getSequenceInfo: function () {
        try {
            if (!app.project) {
                return JSON.stringify({ success: false, error: "No project currently open." });
            }
            var seq = app.project.activeSequence;
            if (!seq) {
                return JSON.stringify({ 
                    success: true, 
                    hasSequence: false, 
                    projectName: app.project.name || "Untitled Project" 
                });
            }

            var timebase = seq.timebase;
            var fps = 25.0;
            if (timebase) {
                fps = parseFloat(timebase) > 0 ? (254016000000 / parseFloat(timebase)) : 25.0;
                if (fps > 100) fps = 25.0; // fallback if tick duration
            }

            return JSON.stringify({
                success: true,
                hasSequence: true,
                projectName: app.project.name,
                sequenceName: seq.name,
                fps: Math.round(fps * 100) / 100,
                videoTrackCount: seq.videoTracks.numTracks,
                audioTrackCount: seq.audioTracks.numTracks
            });
        } catch (e) {
            return JSON.stringify({ success: false, error: e.toString() });
        }
    },

    // 2. Find or Create Bin
    getOrCreateBin: function (binName) {
        var root = app.project.rootItem;
        for (var i = 0; i < root.children.numItems; i++) {
            var item = root.children[i];
            if (item.type === ProjectItemType.BIN && item.name === binName) {
                return item;
            }
        }
        return root.createBin(binName);
    },

    // 3. Import Media Files into Specific Bin
    importFilesToBin: function (binName, pathsArray) {
        try {
            var targetBin = this.getOrCreateBin(binName);
            var prevTarget = app.project.getInsertionBin();
            app.project.setInsertionBin(targetBin);
            app.project.importFiles(pathsArray, 1, targetBin, 0);
            if (prevTarget) {
                app.project.setInsertionBin(prevTarget);
            }
            return JSON.stringify({ success: true, count: pathsArray.length });
        } catch (e) {
            return JSON.stringify({ success: false, error: e.toString() });
        }
    },

    // 4. Lock or Unlock a Video Track
    setTrackLocked: function (trackIndex, isLocked) {
        try {
            var seq = app.project.activeSequence;
            if (!seq || trackIndex >= seq.videoTracks.numTracks) {
                return JSON.stringify({ success: false, error: "Track not found." });
            }
            seq.videoTracks[trackIndex].setLocked(isLocked ? 1 : 0);
            return JSON.stringify({ success: true, track: trackIndex, locked: isLocked });
        } catch (e) {
            return JSON.stringify({ success: false, error: e.toString() });
        }
    },

    // 5. Apply Ultra Key to Video Track
    applyUltraKeyToTrack: function (trackIndex) {
        try {
            var seq = app.project.activeSequence;
            if (!seq) return JSON.stringify({ success: false, error: "No active sequence." });
            
            var track = seq.videoTracks[trackIndex];
            if (!track) return JSON.stringify({ success: false, error: "Video track not found." });

            var count = 0;
            // QE DOM check for native effect application
            if (typeof qe !== "undefined" && qe.project) {
                var qeSeq = qe.project.getActiveSequence();
                if (qeSeq) {
                    var qeTrack = qeSeq.getVideoTrackAt(trackIndex);
                    if (qeTrack) {
                        for (var c = 0; c < qeTrack.numClips; c++) {
                            var clip = qeTrack.getClipAt(c);
                            if (clip) {
                                clip.addVideoEffect(qe.project.getVideoEffectByName("Ultra Key"));
                                count++;
                            }
                        }
                    }
                }
            }

            return JSON.stringify({ success: true, appliedClips: count });
        } catch (e) {
            return JSON.stringify({ success: false, error: e.toString() });
        }
    },

    // 6. Set Motion (Position & Scale)
    setClipMotion: function (trackIndex, clipIndex, posX, posY, scaleVal) {
        try {
            var seq = app.project.activeSequence;
            if (!seq) return JSON.stringify({ success: false, error: "No active sequence." });
            var track = seq.videoTracks[trackIndex];
            var clip = track.clips[clipIndex];
            if (!clip) return JSON.stringify({ success: false, error: "Clip not found." });

            for (var c = 0; c < clip.components.numItems; c++) {
                var comp = clip.components[c];
                if (comp.matchName === "AE.ADBE Motion" || comp.displayName === "Motion") {
                    for (var p = 0; p < comp.properties.numItems; p++) {
                        var prop = comp.properties[p];
                        if (prop.displayName === "Position") {
                            prop.setValue([posX, posY], true);
                        } else if (prop.displayName === "Scale") {
                            prop.setValue(scaleVal, true);
                        }
                    }
                }
            }
            return JSON.stringify({ success: true });
        } catch (e) {
            return JSON.stringify({ success: false, error: e.toString() });
        }
    }
};
