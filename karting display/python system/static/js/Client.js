const GreenFlagButton = document.getElementById('Green-Flag');
const YellowFlagButton = document.getElementById('Yellow-Flag');
const RedFlagButton = document.getElementById("Red-Flag");
const BlueFlagButton = document.getElementById("Blue-Flag");
const pbButton = document.getElementById("PB");
const PitstopButton = document.getElementById("Pitstop");
const ExitButton = document.getElementById("Exit-Command");
const timeSelect = document.getElementById("time");
const positionSelect = document.getElementById("position");

const socket = io('http://localhost:5000');

GreenFlagButton.addEventListener('click', () => {
data = "Green Flag";
console.log(data);
socket.emit("flag_status", data);
})

YellowFlagButton.addEventListener('click', () => {
data = "Yellow Flag";
console.log(data);
socket.emit("flag_status", data);
})

RedFlagButton.addEventListener('click', ( )=> {
data = "Red Flag";
console.log(data);
socket.emit("flag_status", data);
})

BlueFlagButton.addEventListener('click',() => {
data = "Blue Flag";
console.log(data);
socket.emit("flag_status", data);
})

pbButton.addEventListener('click',() => {
data = "PB";
console.log(data);
socket.emit("flag_status", data);
})

PitstopButton.addEventListener('click', () => {
data = "Pitstop";
console.log(data);
socket.emit("flag_status", data);
})

ExitButton.addEventListener('click', () => {
data = "Shutdown";
console.log(data);
socket.emit("flag_status", data);
})

timeSelect.addEventListener("change", () => {
data = `time${timeSelect.value}`;
console.log(data);
socket.emit("flag_status", data);
})
        
positionSelect.addEventListener("change", () => {
data = `pos ${positionSelect.value}`;
console.log(data);
socket.emit("flag_status", data);
})