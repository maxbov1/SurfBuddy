let referenceData = [];
let stages = [];
let currentStageIndex = 0;
let selectedFrames = {};
let uploadedFilename = "";
let selectedReferenceName = "";
let activeCard = null;

const selectFrameBtn = document.getElementById("selectFrameBtn");
const frameSlider = document.getElementById("frameSlider");
const videoPlayer = document.getElementById("videoPlayer");

selectFrameBtn.disabled = true;
frameSlider.disabled = true;
window.onload = () => {
  fetch('/reference')
    .then(response => response.json())
    .then(data => {
      referenceData = data;
      const maneuverContainer = document.getElementById("maneuverCards");
      const techniqueContainer = document.getElementById("techniqueCards");

      referenceData.forEach(ref => {
        const card = document.createElement("div");
        card.className = "card";
        card.innerText = ref.name;
        card.onclick = () => selectReference(ref.name, card);

        if (ref.key_mechanics) {
          maneuverContainer.appendChild(card);
        } else if (ref.key_focus) {
          techniqueContainer.appendChild(card);
        }
      });
    });
  frameSlider.addEventListener("input", () => {
  if (videoPlayer.duration > 0) {
    videoPlayer.currentTime = frameSlider.value;
    if (skeletonActive) {
      captureFrameAndAnalyze();
    }
  }
});

videoPlayer.addEventListener("timeupdate", () => {
  if (skeletonActive) {
    captureFrameAndAnalyze();
  }
});
};

function selectReference(name, cardElement) {
  selectedReferenceName = name; // ✅ Save selected maneuver/technique
  const maneuverObj = referenceData.find(ref => ref.name === name);
  if (!maneuverObj) {
    console.error('❌ Selected reference not found:', name);
    return;
  }
  stages = maneuverObj.frames || [];
  currentStageIndex = 0;
  selectedFrames = {};

  // ✅ Highlight active card
  if (activeCard) {
    activeCard.style.backgroundColor = "#f8f8f8";
    activeCard.style.fontWeight = "normal";
  }
  activeCard = cardElement;
  activeCard.style.backgroundColor = "#b2ebf2"; // Light blue
  activeCard.style.fontWeight = "bold";

  if (stages.length) {
    document.getElementById("currentStageLabel").innerText = `Stage: ${stages[currentStageIndex]}`;
    console.log('✅ Selected:', name, 'Stages:', stages);
  } else {
    document.getElementById("currentStageLabel").innerText = "⚠️ No stages defined.";
  }
}

function uploadVideo() {
  const fileInput = document.getElementById("videoFile");
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  fetch("/upload", {
    method: "POST",
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    uploadedFilename = data.filename.split('.')[0] + "_frames";
    document.getElementById("status").innerText = "✅ Video uploaded! Ready to pick frames.";
    videoPlayer.src = URL.createObjectURL(file);
    videoPlayer.onloadedmetadata = () => {
      frameSlider.max = videoPlayer.duration;  
      frameSlider.step = 0.01;
      frameSlider.value = 0;
      precomputeSkeletons();
    };
  })
  .catch(err => {
    document.getElementById("status").innerText = "❌ Upload failed.";
    console.error(err);
  });
}

frameSlider.addEventListener("input", () => {
  if (videoPlayer.duration > 0) {
    videoPlayer.currentTime = frameSlider.value / 10.0;
    if (skeletonActive) {
      captureFrameAndAnalyze();
    }
  }
});

function selectFrame() {
  if (!stages.length) {
    alert("⚠️ Please select a maneuver or technique first.");
    return;
  }
  const currentStage = stages[currentStageIndex];
  const currentFrameTime = Math.floor(videoPlayer.currentTime * 10);
  selectedFrames[currentStage] = `frame_${String(currentFrameTime).padStart(3, '0')}.jpg`;

  // ✅ Live update selected frames
  document.getElementById("selectedFrames").innerHTML = 
    '<h3>Selected Frames:</h3>' + 
    Object.entries(selectedFrames).map(([stage, frame]) => `<p><b>${stage}</b>: ${frame}</p>`).join('');

  if (currentStageIndex < stages.length - 1) {
    currentStageIndex++;
    document.getElementById("currentStageLabel").innerText = `Stage: ${stages[currentStageIndex]}`;
  } else {
    document.getElementById("status").innerText = "✅ All frames selected. Now submit for feedback.";

  }
}

function submitSelections() {
  const feedbackButton = document.querySelector('button[onclick="submitSelections()"]');

  if (!uploadedFilename) {
    alert("⚠️ Upload a video first!");
    return;
  }
  if (!selectedReferenceName) {
    alert("⚠️ Please select a maneuver or technique first!");
    return;
  }

  console.log('📤 Submitting directly to /pose:', { 
    selectedReferenceName, 
    selectedFrames 
  });

  feedbackButton.disabled = true;
  feedbackButton.innerText = "Analyzing... ⏳";
  document.getElementById("status").innerText = "🔍 Analyzing your technique...";

  fetch("/pose", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      folder_name: uploadedFilename,
      maneuver_name: selectedReferenceName,
      frame_selections: selectedFrames
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      console.error('❌ Pose analysis error:', data.error);
      document.getElementById("status").innerText = "❌ Pose Analysis Failed: " + data.error;
    } else {
      console.log('✅ Pose analysis result:', data);
      document.getElementById("status").innerText = "✅ Pose Analysis Complete! Check console.";
    }
  })
  .catch(err => {
    console.error('❌ Fetch error:', err);
    document.getElementById("status").innerText = "❌ Failed to perform pose analysis.";
  })
  .finally(() => {
    // ✅ Re-enable button after complete
    feedbackButton.disabled = false;
    feedbackButton.innerText = "✅ Get Feedback";
  });
}
let poseLandmarks = null;
let skeletonActive = false;

function checkIfReadyForSkeleton() {
  const overlay = document.getElementById("overlayCanvas");
  overlay.style.display = "block";
  captureFrameAndAnalyze()
}
function captureFrameAndAnalyze() {
  const nearestTime = Math.round(videoPlayer.currentTime * 10) / 10; 
  const landmarks = cachedSkeletons[nearestTime];
  console.log("landmarks:", landmarks)
  if (landmarks) {
    drawSkeletonOnCanvas(landmarks);
    document.getElementById("poseWarning").style.display = "none";
  } else {
    document.getElementById("poseWarning").style.display = "block";
  }
}


// ❌ Clear the overlay if no pose found
function clearSkeleton() {
  const overlay = document.getElementById("overlayCanvas");
  const ctx = overlay.getContext("2d");
  ctx.clearRect(0, 0, overlay.width, overlay.height);
}

// ⚠️ Optional small pose detection warning if no skeleton
function showPoseWarning() {
  const warning = document.getElementById("poseWarning");
  if (warning) {
    warning.style.display = "block";
  }
}

function hidePoseWarning() {
  const warning = document.getElementById("poseWarning");
  if (warning) {
    warning.style.display = "none";
  }
}
function playSlowMotion() {
  if (!uploadedFilename || Object.keys(selectedFrames).length === 0) {
    alert("Please select frames first.");
    return;
  }

  const frameTimes = Object.values(selectedFrames).map(name => {
    const num = parseInt(name.replace("frame_", "").replace(".jpg", ""));
    return num / 10; 
  });

  const minTime = Math.min(...frameTimes);
  const maxTime = Math.max(...frameTimes);

  videoPlayer.currentTime = minTime;
  videoPlayer.playbackRate = 0.5; 
  videoPlayer.play();

}


let cachedSkeletons = {}; 

async function precomputeSkeletons() {
  console.log('🚀 Triggered precompute');
  const frameInterval = 0.1; // every 0.1 seconds
  const frames = [];

  for (let t = 0; t <= videoPlayer.duration; t += frameInterval) {
    frames.push(t);
  }

  console.log(`📋 Frames to process: ${frames.length}`);

  for (const time of frames) {
    console.log(`⏳ Precomputing frame at ${time.toFixed(1)}s`);
    
    videoPlayer.currentTime = time;

    await new Promise(resolve => {
      videoPlayer.onseeked = async () => {
        setTimeout(async () => {  // ✅ ADD this setTimeout(0-100ms) small delay
          const canvas = document.createElement("canvas");
          canvas.width = videoPlayer.videoWidth;
          canvas.height = videoPlayer.videoHeight;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(videoPlayer, 0, 0, canvas.width, canvas.height);

          const dataURL = canvas.toDataURL("image/jpeg");

          try {
            const response = await fetch('/joints_preview', {
              method: "POST",
              headers: {
                "Content-Type": "application/json"
              },
              body: JSON.stringify({ image: dataURL })
            });

            const result = await response.json();
            if (result.pose_detected) {
              cachedSkeletons[Math.round(time * 10) / 10] = result.landmarks;
              console.log(`✅ Pose detected at ${time.toFixed(1)}s`);
            } else {
              console.warn(`⚠️ No pose detected at ${time.toFixed(1)}s`);
            }
          } catch (err) {
            console.error(`❌ Error precomputing at ${time.toFixed(1)}s`, err);
          }
          
          resolve();  // ✅ Move resolve here AFTER timeout
        }, 100); // ✅ Give tiny 100ms delay after seek
      };
    });
  }

  console.log("🔥 Finished precomputing frames");
  console.log("🗂️ Final cachedSkeletons:", cachedSkeletons);

  selectFrameBtn.disabled = false;
  frameSlider.disabled = false;
  document.getElementById("status").innerText = "✅ Poses precomputed! Ready to pick frames.";

  skeletonActive = true;
}


function drawSkeletonOnCanvas(landmarks) {
  console.log("🎯 Drawing skeleton with landmarks:", landmarks);
  const canvas = document.getElementById("overlayCanvas");
  canvas.style.display = "block";  // ✅ Force it visible
  canvas.width = videoPlayer.clientWidth;
  canvas.height = videoPlayer.clientHeight;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  console.log("Canvas size:", canvas.width, canvas.height);

  ctx.fillStyle = "lime";   // Joint points
  ctx.strokeStyle = "red";  // Bone connections
  ctx.lineWidth = 2;

  const connections = [
    // Upper body
    ["point_11", "point_13"], // left shoulder to left elbow
    ["point_13", "point_15"], // left elbow to left wrist
    ["point_12", "point_14"], // right shoulder to right elbow
    ["point_14", "point_16"], // right elbow to right wrist
    ["point_11", "point_12"], // left shoulder to right shoulder
    ["point_11", "point_23"], // left shoulder to left hip
    ["point_12", "point_24"], // right shoulder to right hip
    ["point_23", "point_24"], // left hip to right hip

    // Lower body
    ["point_23", "point_25"], // left hip to left knee
    ["point_25", "point_27"], // left knee to left ankle
    ["point_24", "point_26"], // right hip to right knee
    ["point_26", "point_28"], // right knee to right ankle
  ];

  // Draw bones (lines between landmarks)
  for (const [start, end] of connections) {
    if (landmarks[start] && landmarks[end]) {
      ctx.beginPath();
      ctx.moveTo(landmarks[start][0] * canvas.width, landmarks[start][1] * canvas.height);
      ctx.lineTo(landmarks[end][0] * canvas.width, landmarks[end][1] * canvas.height);
      ctx.stroke();
    }
  }

  // Draw joints (points)
  for (const key in landmarks) {
    const [x, y] = landmarks[key];
    ctx.beginPath();
    ctx.arc(x * canvas.width, y * canvas.height, 5, 0, 2 * Math.PI);
    ctx.fill();
  }
}

