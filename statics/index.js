/* Exapand/Collapse with TAB key */
var expanded = false;
document.onkeydown = function (e) {
    if (e.keyCode === 9) {
        expanded = !expanded;
        document.querySelectorAll("details").forEach(detail => detail.open = expanded);
        return false;
    }
};

const timestamp = document.getElementById("build-timestamp");
const timestamp_local = new Date(timestamp.getAttribute("datetime")).toLocaleString();

const badge = document.getElementById("build-timestamp-badge");
// badge.src = `https://img.shields.io/github/workflow/status/mlnlp-world/myarxiv/Update?=${timestamp_local}&style=for-the-badge`
