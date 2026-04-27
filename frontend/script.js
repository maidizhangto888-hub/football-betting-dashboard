// ... keep the loadPredictions function the same as last time ...

function showDetailModal(match) {
  const modal = document.getElementById('modal');
  const header = document.getElementById('modal-header');
  const content = document.getElementById('modal-content');

  header.innerHTML = `${match.home_team} <span class="text-emerald-400">vs</span> ${match.away_team} <span class="text-sm text-gray-400 ml-4">${match.date} • ${match.league}</span>`;

  let h2hHtml = match.details && match.details.h2h && match.details.h2h.length > 0 
    ? match.details.h2h.map(m => `
        <div class="bg-gray-800 p-4 rounded-2xl text-center">
          <div class="text-xs text-gray-400">${m.date}</div>
          <div>${m.home} ${m.score} ${m.away}</div>
        </div>`).join('')
    : '<div class="bg-gray-800 p-8 rounded-2xl text-center text-gray-400">No recent head-to-head data available yet.<br>This is common early in the season or for less common matchups.</div>';

  let homeFormHtml = match.details && match.details.home_form && match.details.home_form.length > 0 
    ? match.details.home_form.map(f => `
        <div class="bg-gray-800 p-4 rounded-2xl flex justify-between">
          <span>${f.opponent}</span>
          <span class="font-mono">${f.score}</span>
        </div>`).join('')
    : '<div class="text-gray-400 p-6">No recent home form data.</div>';

  let awayFormHtml = match.details && match.details.away_form && match.details.away_form.length > 0 
    ? match.details.away_form.map(f => `
        <div class="bg-gray-800 p-4 rounded-2xl flex justify-between">
          <span>${f.opponent}</span>
          <span class="font-mono">${f.score}</span>
        </div>`).join('')
    : '<div class="text-gray-400 p-6">No recent away form data.</div>';

  const html = `
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div>
        <h3 class="font-semibold mb-4 text-lg">xG Preview</h3>
        <div class="bg-gray-800 rounded-2xl p-6 space-y-4">
          <div class="flex justify-between items-center">
            <span>Home xG</span>
            <span class="font-mono text-2xl text-emerald-400">${match.home_xg}</span>
          </div>
          <div class="flex justify-between items-center">
            <span>Away xG</span>
            <span class="font-mono text-2xl">${match.away_xg}</span>
          </div>
          <div class="pt-4 border-t border-gray-700 grid grid-cols-3 text-center">
            <div><div class="text-emerald-400 font-bold text-xl">${(match.home_win_prob*100).toFixed(0)}%</div><div class="text-xs">HOME</div></div>
            <div><div class="font-bold text-xl">${(match.draw_prob*100).toFixed(0)}%</div><div class="text-xs">DRAW</div></div>
            <div><div class="text-red-400 font-bold text-xl">${(match.away_win_prob*100).toFixed(0)}%</div><div class="text-xs">AWAY</div></div>
          </div>
        </div>
      </div>

      <div>
        <h3 class="font-semibold mb-4 text-lg">Value Bets</h3>
        <div class="space-y-3">
          ${ (match.value_home || 0) > 0 ? `<div class="bg-emerald-500 text-black p-5 rounded-2xl font-semibold">HOME +${(match.value_home*100).toFixed(1)}% EDGE</div>` : ''}
          ${ (match.value_draw || 0) > 0 ? `<div class="bg-emerald-500 text-black p-5 rounded-2xl font-semibold">DRAW +${(match.value_draw*100).toFixed(1)}% EDGE</div>` : ''}
          ${ (match.value_away || 0) > 0 ? `<div class="bg-emerald-500 text-black p-5 rounded-2xl font-semibold">AWAY +${(match.value_away*100).toFixed(1)}% EDGE</div>` : ''}
          ${ (match.value_home || 0) === 0 && (match.value_draw || 0) === 0 && (match.value_away || 0) === 0 ? '<div class="text-gray-400 p-6">No strong value bets detected for this match.</div>' : ''}
        </div>
      </div>
    </div>

    <div class="mt-12">
      <h3 class="font-semibold mb-4">Head-to-Head (recent)</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        ${h2hHtml}
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mt-12">
      <div>
        <h3 class="font-semibold mb-4">${match.home_team} Recent Home Form</h3>
        <div class="space-y-3">${homeFormHtml}</div>
      </div>
      <div>
        <h3 class="font-semibold mb-4">${match.away_team} Recent Away Form</h3>
        <div class="space-y-3">${awayFormHtml}</div>
      </div>
    </div>
  `;

  content.innerHTML = html;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

// Keep the rest of the file (loadPredictions, closeModal, etc.) the same as your current version
