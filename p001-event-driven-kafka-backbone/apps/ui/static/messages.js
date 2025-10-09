// messages.js - Handles fetching and displaying Kafka topic messages in the UI

/**
 * Fetch messages from the backend and update all tables.
 */
function fetchMessages() {
    fetch('/messages')
        .then(response => response.json())
        .then(data => {
            updateTable('messages-table', data.orders);
            updateTable('retry-table', data.retry);
            updateTable('dlq-table', data.dlq);
        });
}

/**
 * Update a table with messages.
 * @param {string} tableId - The ID of the table to update.
 * @param {Array} messages - Array of message objects.
 */
function updateTable(tableId, messages) {
    const tbody = document.getElementById(tableId).getElementsByTagName('tbody')[0];
    tbody.innerHTML = '';
    messages.forEach(msg => {
        const row = tbody.insertRow();
        row.insertCell(0).innerText = msg.key;
        row.insertCell(1).innerText = msg.value;
        row.insertCell(2).innerText = msg.partition;
        row.insertCell(3).innerText = msg.offset;
        row.insertCell(4).innerText = new Date(msg.timestamp).toLocaleString();
    });
}

// Periodically refresh tables every second
setInterval(fetchMessages, 1000);
window.onload = fetchMessages;

/**
 * Handle AJAX form submission for producing messages.
 */
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('produce-form');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(form);
        const amountValue = formData.get('value');
        // Convert to JSON string for backend
        const jsonValue = JSON.stringify({ amount: parseFloat(amountValue) });
        formData.set('value', jsonValue);
        fetch('/produce', {
            method: 'POST',
            body: formData
        }).then(() => {
            form.reset();
        });
    });
});