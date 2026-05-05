const navbar = document.querySelector("nav");
const navbutton = document.getElementById("nav-hide");

navbutton.addEventListener("click", () => {
	if (navbar.style.display != "none") {
		navbar.style.minWidth = 0 + "rem";
		navbar.style.width = 0 + "rem";
		navbar.style.display = "none";
	} else {
		navbar.style.minWidth = 16 + "rem";
		navbar.style.width = 16 + "rem";
		navbar.style.display = "inline-flex";
	}
});