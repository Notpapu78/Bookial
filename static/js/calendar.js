document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    
    if (calendarEl) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'es',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,listMonth'
            },
            events: '/api/calendar',
            eventClick: function(info) {
                if (confirm(`¿Marcar como devuelto: ${info.event.title}?`)) {
                    // Lógica para devolver libro
                    fetch('/api/return_book', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ event_id: info.event.id })
                    }).then(() => {
                        info.event.remove();
                        alert('Libro devuelto exitosamente');
                    });
                }
            },
            eventDidMount: function(info) {
                // Añadir tooltip
                info.el.setAttribute('title', info.event.title);
            }
        });
        
        calendar.render();
    }
});