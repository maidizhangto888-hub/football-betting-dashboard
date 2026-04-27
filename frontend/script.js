async function loadPredictions() {
  const response = await fetch('https://raw.githubusercontent.com/Proofmaster/football-betting-dashboard/main/data/predictions.json');
  const matches = await response.json();
  
  const container = document.getElementById('matches');
  container.innerHTML = '';

  // Summary
  const total = matches.length;
  const valueCount = matches.filter(m => Math.max(m.value_home, m.value_draw, m.value_away) > 0).length;
  document.getElementById('summary').innerHTML = `
    <div class="bg-gray-900 p-6 rounded-2xl text-center"><div class="text-emerald-400 text-sm">MATCHES</div><div class="text-5xl font-bold">${total}</div></div>
    <div class="bg-gray-900 p-6 rounded-2xl text-center"><div class="text-emerald-400 text-sm">VALUE BETS</div><div class="text-5xl font-bold text-emerald-400">${valueCount}</div></div>
    <div class="bg-gray-900 p-6 rounded-2xl text-center"><div class="text-emerald-400 text-sm">AVG HOME xG</div><div class="text-5xl font-bold">${(matches.reduce((s,m)=>s+m.home_xg,0)/total).toFixed(1)}</div></div>
    <div class="bg-gray-900 p-6 rounded-2xl text-center"><div class="text-emerald-400 text-sm">OVER 2.5 AVG</div><div class="text-5xl font-bold">${(matches.reduce((s,m)=>s+m.over_25_prob,0)/total*100).toFixed(0)}%</div></div>
  `;

  matches.forEach((match, index) => {
    const card = document.createElement('div');
    card.className = 'bg-gray-900 rounded-3xl p-6 cursor-pointer hover:scale-[1.02] transition-all border border-gray-700 hover:border-emerald-500';
    card.innerHTML = `
      <div class="flex justify-between items-start">
        <div>
          <span class="px-3 py-1 bg-gray-800 text-xs rounded-full">${match.league}</span>
          <div class="text-xl font-semibold mt-3">${match.home_team} vs ${match.away_team}</div>
          <div class="text-sm text-gray-400">${match.date}</div>
        </div>
        <div class="text-right">
          <div class="text-emerald-400 font-bold">${match.home_xg} – ${match.away_xg} xG</div>
          ${Math.max(match.value_home, match.value_draw, match.value_away) > 0 ? `<div class="text-xs bg-emerald-500 text-black px-3 py-1 rounded-full inline-block mt-2">+${(Math.max(match.value_home, match.value_draw, match.value_away)*100).toFixed(1)}% EDGE</div>` : ''}
        </div>
      </div>
      <div class="grid grid-cols-3 gap-4 mt-6 text-center text-sm">
        <div><div class="text-emerald-400">${(match.home_win_prob*100).toFixed(0)}%</div><div class="text-xs text-gray-400">HOME</div></div>
        <div><div>${(match.draw_prob*100).toFixed(0)}%</div><div class="text-xs text-gray-400">DRAW</div></div>
        <div><div class="text-red-400">${(match.away_win_prob*100).toFixed(0)}%</div><div class="text-xs text-gray-400">AWAY</div></div>
      </div>
    `;
    card.onclick = () => showDetailModal(match);
    container.appendChild(card);
  });
}

function showDetailModal(match) {
  const modal = document.getElementById('modal');
  const header = document.getElementById('modal-header');
  const content = document.getElementById('modal-content');

  header.innerHTML = `${match.home_team} vs ${match.away_team} <span class="text-sm text-gray-400 ml-4">${match.date} • ${match.league}</span>`;

  let html = `
    <div class="grid grid-cols-2 gap-8">
      <!-- Preview -->
      <div>
        <h3 class="font-semibold mb-4">Match Preview</h3>
        <div class="bg-gray-800 rounded-2xl p-5 space-y-4">
          <div class="flex justify-between"><span>Home xG</span><span class="font-mono">${match.home_xg}</span></div>
          <div class="flex justify-between"><span>Away xG</span><span class="font-mono">${match.away_xg}</span></div>
          <div class="h-2 bg-gray-700 rounded-full overflow-hidden"><div class="h-full bg-emerald-500" style="width: ${match.home_win_prob*100}%"></div></div>
          <div class="grid grid-cols-3 text-center text-sm">
            <div>Home ${ (match.home_win_prob*100).toFixed(0) }%</div>
            <div>Draw ${ (match.draw_prob*100).toFixed(0) }%</div>
            <div>Away ${ (match.away_win_prob*100).toFixed(0) }%</div>
          </div>
          <div class="text-xs text-emerald-400">Over 2.5 goals: ${(match.over_25_prob*100).toFixed(0)}%</div>
        </div>
      </div>

      <!-- Value bets -->
      <div>
        <h3 class="font-semibold mb-4">Value Bets</h3>
        ${match.value_home > 0 ? `<div class="bg-emerald-500 text-black px-4 py-3 rounded-2xl mb-2">HOME +${(match.value_home*100).toFixed(1)}% edge</div>` : ''}
        ${match.value_draw > 0 ? `<div class="bg-emerald-500 text-black px-4 py-3 rounded-2xl mb-2">DRAW +${(match.value_draw*100).toFixed(1)}% edge</div>` : ''}
        ${match.value_away > 0 ? `<div class="bg-emerald-500 text-black px-4 py-3 rounded-2xl">AWAY +${(match.value_away*100).toFixed(1)}% edge</div>` : ''}
      </div>
    </div>

    <!-- H2H -->
    <div class="mt-10">
      <h3 class="font-semibold mb-4">Head-to-Head (last 6)</h3>
      <div class="grid grid-cols-3 gap-2 text-sm">
        ${match.details.h2h.map(m => `
          <div class="bg-gray-800 p-3 rounded-2xl text-center">
            ${m.date}<br>
            ${m.home} ${m.score} ${m.away}
          </div>`).join('')}
      </div>
    </div>

    <!-- Form -->
    <div class="grid grid-cols-2 gap-8 mt-10">
      <div>
        <h3 class="font-semibold mb-4">${match.home_team} Recent Form (Home)</h3>
        ${match.details.home_form.map(f => `<div class="flex justify-between bg-gray-800 p-3 rounded-2xl mb-2"><span>${f.opponent}</span><span>${f.score}</span></div>`).join('')}
      </div>
      <div>
        <h3 class="font-semibold mb-4">${match.away_team} Recent Form (Away)</h3>
        ${match.details.away_form.map(f => `<div class="flex justify-between bg-gray-800 p-3 rounded-2xl mb-2"><span>${f.opponent}</span><span>${f.score}</span></div>`).join('')}
      </div>
    </div>
  `;

  content.innerHTML = html;
  modal.classList.remove('hidden');
  modal.classList.add('flex');
}

function closeModal() {
  const modal = document.getElementById('modal');
  modal.classList.add('hidden');
  modal.classList.remove('flex');
}

loadPredictions();
