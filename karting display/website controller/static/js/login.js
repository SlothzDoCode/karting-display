const socket = io("http://localhost:5000");
const selectSignUpBtn = document.getElementById("signUp");
const selectLogInBtn = document.getElementById("signIn");
const loginBtn = document.getElementById("get-logIn");
const signupBtn = document.getElementById("get-signUp");

socket.on("connect", () => {
    console.log("Connected to server:", socket.id);
});
socket.on("login_response", (data) =>{
    console.log(data);
    if (data === "valid login"){
        window.location.href = "/templates/index.html";
    }
});

selectSignUpBtn.addEventListener('click', () => {
    container.classList.add("right-panel-active");
});

selectLogInBtn.addEventListener('click', () => {
    container.classList.remove("right-panel-active");
});

loginBtn.addEventListener('click', () => {
    uName_input = document.getElementById('uname').value;
    password_input = document.getElementById('password').value;
    return_array = [uName_input, password_input]
    socket.emit("login_handle_input", return_array);
});

signupBtn.addEventListener('click', () => {
    console.log(1, "something is broken")
});