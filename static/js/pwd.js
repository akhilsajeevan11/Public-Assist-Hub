document.addEventListener("DOMContentLoaded", function () {
    fetchIssues();
});

function fetchIssues() {
    fetch("/api/issues/pwd")
        .then(response => response.json())
        .then(data => {
            displayIssues(data);
        })
        .catch(error => console.error("Error fetching PWD issues:", error));
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
    .then(() => window.location.reload())
    .catch(error => console.error("Error updating status:", error));
}

function deleteIssue(issueId) {
    if (confirm("Are you sure you want to delete this issue?")) {
        fetch(`/api/issues/${issueId}`, {
            method: "DELETE"
        })
        .then(response => response.json())
        .then(() => fetchIssues())
        .catch(error => console.error("Error deleting issue:", error));
    }
}

function resolveIssue(issueId) {
    if (confirm("Are you sure you want to mark this issue as resolved?")) {
        fetch(`/api/issues/${issueId}/resolve`, {
            method: "PUT"
        })
        .then(response => response.json())
        .then(() => window.location.reload())
        .catch(error => console.error("Error resolving issue:", error));
    }
}

function checkIssue(issueId) {
    fetch(`/api/issues/${issueId}/check`, {
        method: "PUT"
    })
    .then(response => response.json())
    .then(() => window.location.reload())
    .catch(error => console.error("Error checking issue:", error));
}
