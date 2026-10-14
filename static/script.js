
const teamInput = document.querySelector('textarea[name="teams"]');
const form = document.querySelector('form');

// Create a team counter
const counter = document.createElement('p');
counter.style.color = '#174ea6';
counter.style.fontSize = '14px';
counter.style.marginTop = '8px';

teamInput.insertAdjacentElement('afterend', counter);

function updateTeamCount() {
    const teams = teamInput.value
        .split('\n')
        .map(team => team.trim())
        .filter(team => team.length > 0);

    counter.textContent = `Teams entered: ${teams.length}`;
}

teamInput.addEventListener('input', updateTeamCount);

form.addEventListener('submit', function (event) {
    const teams = teamInput.value
        .split('\n')
        .map(team => team.trim())
        .filter(team => team.length > 0);

    if (teams.length < 2) {
        event.preventDefault();
        alert('Please enter at least 2 teams!');
    }
});

updateTeamCount();
