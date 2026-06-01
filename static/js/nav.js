// Smooth scrolling and nav interactions
document.addEventListener('DOMContentLoaded', function() {
	// Auto-hide alerts after 5 seconds
	setTimeout(() => {
		document.querySelectorAll('.alert').forEach(alert => {
			alert.style.opacity = '0';
			setTimeout(() => alert.remove(), 300);
		});
	}, 5000);
});

// Función para confirmar acciones
function confirmAction(message, url) {
	if (confirm(message)) {
		window.location.href = url;
	}
	return false;
}
