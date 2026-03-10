//other constants
const socket = io("http://172.24.36.89:5000");
const trackSelect = document.getElementById("location");
const mapDiv = document.querySelector(".map");

//options bar constants
const homeBtn = document.getElementById("home");
const logoutBtn = document.getElementById("logout");

//create the consts that are used to send data to the server and display
const greenFlg = document.getElementById("Green-Flag");
const yellowFlg = document.getElementById("Yellow-Flag");
const redFlg = document.getElementById("Red-Flag");
const blueFlg = document.getElementById("Blue-Flag");
const PBAlert = document.getElementById("PB");
const PitsopAlert = document.getElementById("Pitstop");
const timeSelect = document.getElementById("time");
const positionSelect = document.getElementById("position");

//dictionary containing track map locations

socket.on("connect", () => {
    console.log("Connected!");
    socket.emit("connected", { hello: "world" });
});

socket.on("Track-setup", (data) => {
    console.log(data); 
    const tracks = data.map(sub => sub[0]);
    tracks.sort((a, b) => a.localeCompare(b));
    const placeholder = trackSelect.querySelector('option[disabled]');
    trackSelect.innerHTML = "";
    if (placeholder) trackSelect.appendChild(placeholder);
    tracks.forEach(track => {
        const el = document.createElement("option");
        el.textContent = track;
        el.value = track;
        trackSelect.appendChild(el);
    });
});

socket.on("return-values", (data) => {
    console.log(data);

    mapDiv.innerHTML = "";

    const img = document.createElement("img");
    img.src = data;
    img.alt = "Track Map";
    img.style.maxWidth = "100%";
    img.style.height = "auto";

    mapDiv.appendChild(img);
});

greenFlg.addEventListener('click', () => {
    console.log("green_flag");
    socket.emit("index_handle_input", "green-flag");
});

yellowFlg.addEventListener('click', () => {
    console.log("yellow_flag");
    socket.emit("index_handle_input", "yellow-flag");
});

redFlg.addEventListener('click', () => {
    console.log("red_flag");
    socket.emit("index_handle_input", "red-flag");
});

blueFlg.addEventListener('click', () => {
    console.log("blue_flag");
    socket.emit("index_handle_input", "blue-flag");
});

PBAlert.addEventListener('click', () => {
    console.log("PB_alert");
    socket.emit("index_handle_input", "PB-alert");
});

PitsopAlert.addEventListener('click', () => {
    console.log("pitstop_alert");
    socket.emit("index_handle_input", "pitstop-alert");
});

trackSelect.addEventListener('change', function() {
    const selectedValue = this.value;
    console.log(selectedValue);
    socket.emit("index_handle_input", selectedValue);
});

timeSelect.addEventListener("change", () => {
data = `time${timeSelect.value}`;
console.log(data);
socket.emit("index_handle_input", data);
})
        
positionSelect.addEventListener("change", () => {
data = `pos ${positionSelect.value}`;
console.log(data);
socket.emit("index_handle_input", data);
})

homeBtn.addEventListener('click', () => {
    window.location.href = "/templates/index.html";
});

logoutBtn.addEventListener('click', () => {
    window.location.href = "/templates/login.html";
});


// ===================== Bug Report Modal ===================== //
const bugModal = document.getElementById("bug-modal");
const openBugBtn = document.getElementById("bug-report"); // Sidebar button
const closeBugBtn = document.getElementById("close-bug-modal");

const bugTitleInput = document.getElementById("bug-title");
const bugDescriptionInput = document.getElementById("bug-description");
const submitBugBtn = document.getElementById("submit-bug");
const bugStatus = document.getElementById("bug-status");

// Open modal
openBugBtn.addEventListener("click", () => {
    bugModal.style.display = "flex";
    bugStatus.textContent = "";
    bugTitleInput.value = "";
    bugDescriptionInput.value = "";
});

// Close modal
closeBugBtn.addEventListener("click", () => {
    bugModal.style.display = "none";
});

// Close modal if clicking outside content
window.addEventListener("click", (e) => {
    if (e.target === bugModal) {
        bugModal.style.display = "none";
    }
});

// Submit bug report
submitBugBtn.addEventListener("click", () => {
    const title = bugTitleInput.value.trim();
    const description = bugDescriptionInput.value.trim();

    if (!title || !description) {
        bugStatus.textContent = "Please fill in both title and description.";
        bugStatus.style.color = "red";
        return;
    }

    const payload = {
        title,
        description,
        user_agent: navigator.userAgent,
        url: window.location.href
    };

    socket.emit("bug_report", payload);
    bugStatus.textContent = "Sending...";
    bugStatus.style.color = "black";
});

// Receive confirmation from server
socket.on("bug_report_status", (data) => {
    if (data.status === "ok") {
        bugStatus.textContent = "Bug report submitted! Thank you.";
        bugStatus.style.color = "green";
        bugTitleInput.value = "";
        bugDescriptionInput.value = "";
        setTimeout(() => { bugModal.style.display = "none"; }, 2000); // auto-close after 2s
    } else {
        bugStatus.textContent = "Failed to submit bug report.";
        bugStatus.style.color = "red";
    }
});
