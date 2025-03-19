document.addEventListener("DOMContentLoaded", function () {
    fetchIssues();
    refreshCounts(); // Fetch counts on page load
});

function fetchIssues() {
    fetch("/api/issues/municipality") // Use the correct API endpoint for Municipality issues
        .then(response => response.json())
        .then(data => {
            displayIssues(data);
        })
        .catch(error => console.error("Error fetching issues:", error));
}

function displayIssues(issues) {
    const issueList = document.getElementById("issue-list");
    issueList.innerHTML = "";

    issues.forEach(issue => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${issue.id}</td>
            <td>${issue.category}</td>
            <td>${issue.description}</td>
            <td>
                <select class="form-control" onchange="updateStatus(${issue.id}, this.value)">
                    <option value="Pending" ${issue.status === "Pending" ? "selected" : ""}>Pending</option>
                    <option value="In Progress" ${issue.status === "In Progress" ? "selected" : ""}>In Progress</option>
                    <option value="Resolved" ${issue.status === "Resolved" ? "selected" : ""}>Resolved</option>
                </select>
            </td>
            <td>
                <button class="btn btn-success" onclick="resolveIssue(${issue.id})">Resolve</button>
                <button class="btn btn-info" onclick="checkIssue(${issue.id})">Check</button>
            </td>
        `;
        issueList.appendChild(row);
    });
}

function updateStatus(issueId, newStatus) {
    fetch(`/api/issues/${issueId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => response.json())
    .then(() => {
        fetchIssues(); // Refresh the issue list
        refreshCounts(); // Refresh the counts
    })
    .catch(error => console.error("Error updating status:", error));
}

function deleteIssue(issueId) {
    if (confirm("Are you sure you want to delete this issue?")) {
        fetch(`/api/issues/${issueId}`, {
            method: "DELETE"
        })
        .then(response => response.json())
        .then(() => {
            fetchIssues(); // Refresh the issue list
            refreshCounts(); // Refresh the counts
        })
        .catch(error => console.error("Error deleting issue:", error));
    }
}

function resolveIssue(issueId) {
    if (confirm("Are you sure you want to mark this issue as resolved?")) {
        fetch(`/api/issues/${issueId}/resolve`, {
            method: "PUT"
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert("Issue resolved successfully!");
                window.location.reload();
                fetchIssues(); // Refresh the issue list
                refreshCounts(); // Refresh the counts
            } else {
                alert("Failed to resolve issue: " + data.message);
            }
        })
        .catch(error => console.error("Error resolving issue:", error));
    }
}

function checkIssue(issueId) {
    fetch(`/api/issues/${issueId}/check`, {
        method: "PUT"
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Issue checked successfully!");
            fetchIssues(); // Refresh the issue list
            refreshCounts(); // Refresh the counts
        } else {
            alert("Failed to check issue: " + data.message);
        }
    })
    .catch(error => console.error("Error checking issue:", error));
}

function refreshCounts() {
    fetch("/api/issues/counts/municipality") // Use the correct API endpoint for Municipality counts
        .then(response => response.json())
        .then(data => {
            // Update the counts in the HTML
            document.querySelector(".card-title:contains('Pending Issues') + .display-4").textContent = data.pending_count;
            document.querySelector(".card-title:contains('Resolved Issues') + .display-4").textContent = data.resolved_count;
        })
        .catch(error => console.error("Error refreshing counts:", error));
}
