// JavaScript code for ticket management

// Function to toggle visibility of comments section
function toggleComments() {
    var commentsSection = document.getElementById('comments-section');
    commentsSection.classList.toggle('hidden');
}

// Function to handle file upload
function handleFileUpload() {
    var fileInput = document.getElementById('attachment-input');
    var fileList = fileInput.files;

    // Display selected file names
    var fileNames = "";
    for (var i = 0; i < fileList.length; i++) {
        fileNames += fileList[i].name;
        if (i < fileList.length - 1) {
            fileNames += ", ";
        }
    }
    var fileNameDisplay = document.getElementById('attachment-names');
    fileNameDisplay.textContent = fileNames;
}
function test(){
    console.log("This is a message printed to the console");
}
function showAllTickets(ticketData) {
    const ticketList = document.getElementById('ticketList');
    ticketList.innerHTML = ''; // Clear existing ticket list

    // Parse the ticket data into an array of JavaScript objects
    const tickets = ticketData.map(ticket => {
        // Convert 'None' values to null in each ticket object
        Object.keys(ticket).forEach(key => {
            if (ticket[key] === 'None') {
                ticket[key] = null;
            }
        });
        return ticket;
    });

    // Check if tickets is not null
    if (tickets.length > 0) {
        tickets.forEach(ticket => {
            const listItem = document.createElement('li');
            listItem.classList.add('ticket-item');

            // Create separate divs for ticket number, description, and assignee
            const ticketNumber = document.createElement('div');
            ticketNumber.textContent = ticket.ticket_number ? `Ticket Number: ${ticket.ticket_number}` : 'Ticket Number: Unknown';
            listItem.appendChild(ticketNumber);

            const description = document.createElement('div');
            description.textContent = ticket.description ? `Description: ${ticket.description}` : 'Blank';
            listItem.appendChild(description);

            const assignee = document.createElement('div');
            const assigneeText = ticket.assignee ? `Assignee: ${ticket.assignee}` : 'Unassigned';
            assignee.textContent = assigneeText;
            listItem.appendChild(assignee);

            // Create a link to the ticket details page
            const link = document.createElement('a');
            link.href = `/ticket/${ticket.id}`; 
            link.textContent = 'View Details';
            listItem.appendChild(link);

            ticketList.appendChild(listItem);
        });
    } else {
        // If tickets is empty, display a message indicating no tickets
        const listItem = document.createElement('li');
        listItem.textContent = 'No tickets available';
        ticketList.appendChild(listItem);
    }
}


function showMyTickets(ticketData, currentUser) {
    const ticketList = document.getElementById('ticketList');
    ticketList.innerHTML = ''; // Clear existing ticket list

    // Filter tickets assigned to the current user
    const myTickets = ticketData.filter(ticket => String(ticket.assignee) === String(currentUser));

    // Check if there are any tickets assigned to the current user
    if (myTickets && myTickets.length > 0) {
        myTickets.forEach(ticket => {
            const listItem = document.createElement('li');
            listItem.classList.add('ticket-item');

            // Create separate divs for ticket number, description, and assignee
            const ticketNumber = document.createElement('div');
            ticketNumber.textContent = ticket.ticket_number ? `Ticket Number: ${ticket.ticket_number}` : 'Ticket Number: Unknown';
            listItem.appendChild(ticketNumber);

            const description = document.createElement('div');
            description.textContent = ticket.description ? `Description: ${ticket.description}` : 'Blank';
            listItem.appendChild(description);

            const assignee = document.createElement('div');
            const assigneeText = ticket.assignee ? `Assignee: ${ticket.assignee}` : 'Unassigned';
            assignee.textContent = assigneeText;
            listItem.appendChild(assignee);

            // Create a link to the ticket details page
            const link = document.createElement('a');
            link.href = `/ticket/${ticket.id}`; 
            link.textContent = 'View Details';
            listItem.appendChild(link);

            ticketList.appendChild(listItem);
        });
    } else {
        // If no tickets are assigned to the current user, display a message
        const listItem = document.createElement('li');
        listItem.textContent = 'No tickets assigned to you';
        ticketList.appendChild(listItem);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Get the profile picture and the logout dropdown content
    var profilePicture = document.getElementById('profile-picture');
    var logoutDropdown = document.getElementById('logout-dropdown');

    // Add click event listener to the profile picture
    profilePicture.addEventListener('click', function(event) {
        // Toggle the visibility of the logout dropdown content
        logoutDropdown.style.display = logoutDropdown.style.display === 'block' ? 'none' : 'block';
    });
});







