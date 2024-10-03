document.addEventListener('DOMContentLoaded', function () {
    // Handle Report Generation Form
    const generateForm = document.getElementById('stock-form');
    const spinner = document.getElementById('loading-spinner');
    
    if (generateForm) {
        const generateSubmitButton = generateForm.querySelector('button[type="submit"]');

        generateForm.addEventListener('submit', function () {
            generateSubmitButton.disabled = true;
            if (spinner) spinner.style.display = 'flex';
        });
    }

    // Handle Save Report Form
    const saveForm = document.getElementById('save-report-form');
    if (saveForm) {
        const saveSubmitButton = saveForm.querySelector('button[type="submit"]');
        saveForm.addEventListener('submit', function () {
            saveSubmitButton.disabled = true;
            if (spinner) spinner.style.display = 'flex';
        });
    }

    // Handle Delete Report Forms
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(function (form) {
        const deleteButton = form.querySelector('button[type="submit"]');
        form.addEventListener('submit', function () {
            deleteButton.disabled = true;
            if (spinner) spinner.style.display = 'flex';
        });
    });

    // Add hover effect for report cards
    const reportCards = document.querySelectorAll('.report-card');
    reportCards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const midX = rect.width / 2;
            const midY = rect.height / 2;

            const translateX = ((x - midX) / midX) * 10;
            const translateY = ((y - midY) / midY) * 10;

            // Move the card
            card.style.transform = `translate(${translateX}px, ${translateY}px)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translate(0px, 0px)';
        });
    });

    // Apply hover effect to initial content box
    const initialContent = document.querySelector('.initial-content');
    if (initialContent) {
        initialContent.addEventListener('mousemove', (e) => {
            const rect = initialContent.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const midX = rect.width / 2;
            const midY = rect.height / 2;

            const translateX = ((x - midX) / midX) * 10;
            const translateY = ((y - midY) / midY) * 10;

            initialContent.style.transform = `translate(${translateX}px, ${translateY}px)`;
        });

        initialContent.addEventListener('mouseleave', () => {
            initialContent.style.transform = 'translate(0px, 0px)';
        });
    }
})

const hamburgerMenu = document.querySelector('.hamburger-menu');
const sidebar = document.querySelector('.sidebar');
const mainContent = document.querySelector('.main-content');

hamburgerMenu.addEventListener('click', function() {
    sidebar.classList.toggle('visible');
    mainContent.classList.toggle('expanded');
});
