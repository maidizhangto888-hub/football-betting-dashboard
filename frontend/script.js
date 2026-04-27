async function loadPredictions() {
  try {
    const response = await fetch('https://raw.githubusercontent.com/Proofmaster/football-betting-dashboard/main/data/predictions.json');
    const matches = await response.json();
    
    const container = document.getElementById('matches');
    container.innerHTML = '';

    if (matches.length === 0) {
      container.innerHTML = '<p class="text-gray-400 text-center py-12">No matches right now.</p>';
      return;
    }

    // Summary
    const total = matches.length;
    const valueCount = matches.filter(m => Math.max(m.value_home, m.value_draw, m.value_away) > 0).length;
    document.getElementById('summary').innerHTML = `
      <div class="bg-gray-900 p-6 rounded-2xl"><div class="text-emerald-400 text-sm">MATCHES</div><div class="text-4xl font-bold">${total}</div></div>
      <div class="bg-gray-900 p-6 rounded-2xl"><div class="text-emerald-400 text-sm">VALUE BETS</div><div class="text-4xl font-bold text-emerald-400">${valueCount}</div></div>
      <div class="bg-gray-900 p-6 rounded-2xl"><div class="text-emerald-400 text-sm">AVG HOME xG</div><div class="text-4xl font-bold">${(matches.reduce((s,m)=>s+m.home_xg,0)/total).toFixed(1)}</div></div>
      <div class="bg-gray-900 p-6 rounded-2xl"><div class="text-emerald-400 text-sm">OVER 2.5 AVG</div><div class="text-4xl font-bold">${(matches.reduce((s,m)=>s+m.over_25_prob,0)/total*100).toFixed(0)}%</div></div>
    `;

    matches.forEach((match, index) => {
      const hasValue = Math.max(match.value_home, match.value_draw, match.value_away) > 0;
      const card = document.createElement('div');
      card.className = `bg-gray-900 rounded-3xl p-8 border ${hasValue ? 'border-emerald-500' : 'border-gray-700'}`;

      card.innerHTML = `
        <div class="flex justify-between mb-6">
          <div>
            <span class="px-3 py-1 bg-gray-800 rounded-full text-xs">${match.league}</span>
            <div class="text-2xl font-semibold mt-3">${match.home_team} vs ${match.away_team}</div>
            <div class="text-gray-400">${match.date}</div>
          </div>
          ${hasValue ? `<div class="text-emerald-400 font-bold text-xl">+${(Math.max(match.value_home, match.value_draw, match.value_away)*100).toFixed(1)}% EDGE</div>` : ''}
        </div>

        <div class="grid grid-cols-2 md:grid-cols-5 gap-6">
          <!-- xG -->
          <div class="text-center">
            <div class="text-xs text-gray-400">HOME xG</div>
            <div class="text-5xl font-bold text-emerald-400">${match.home_xg}</div>
          </div>
          <div class="text-center">
            <div class="text-xs text-gray-400">AWAY xG</div>
            <div class="text-5xl font-bold">${match.away_xg}</div>
          </div>

          <!-- Probabilities with mini bars -->
          <div class="col-span-3">
            <div class="space-y-4">
              <div>
                <div class="flex justify-between text-sm"><span>Home Win</span><span>${(match.home_win_prob*100).toFixed(0)}%</span></div>
                <div class="h-3 bg-gray-800 rounded-full overflow-hidden"><div class="h-full bg-emerald-500" style="width: ${match.home_win_prob*100}%"></div></div>
              </div>
              <div>
                <div class="flex justify-between text-sm"><span>Draw</span><span>${(match.draw_prob*100).toFixed(0)}%</span></div>
                <div class="h-3 bg-gray-800 rounded-full overflow-hidden"><div class="h-full bg-gray-400" style="width: ${match.draw_prob*100}%"></div></div>
              </div>
              <div>
                <div class="flex justify-between text-sm"><span>Away Win</span><span>${(match.away_win_prob*100).toFixed(0)}%</span></div>
                <div class="h-3 bg-gray-800 rounded-full overflow-hidden"><div class="h-full bg-red-500" style="width: ${match.away_win_prob*100}%"></div></div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-8">
          <canvas id="chart-${index}" width="400" height="120"></canvas>
        </div>

        <div class="mt-6 grid grid-cols-3 gap-4 text-center text-sm">
          <div>Home Odds: <span class="font-mono">${match.home_odds.toFixed(2)}</span></div>
          <div>Draw: <span class="font-mono">${match.draw_odds.toFixed(2)}</span></div>
          <div>Away: <span class="font-mono">${match.away_odds.toFixed(2)}</span></div>
        </div>
      `;

      container.appendChild(card);

      // Simple expected scoreline bar chart
      setTimeout(() => {
        const ctx = document.getElementById(`chart-${index}`);
        if (ctx) {
          new Chart(ctx, {
            type: 'bar',
            data: {
              labels: ['0-0', '1-0', '1-1', '2-1', '2-0', '0-1', 'Other'],
              datasets: [{
                label: 'Prob %',
                data: [15, 20, 18, 12, 10, 8, 17], // Placeholder — can be calculated dynamically later
                backgroundColor: '#10b981'
              }]
            },
            options: { scales: { y: { beginAtZero: true } }, plugins: { legend: { display: false } } }
          });
        }
      }, 100);
    });

  } catch (e) {
    console.error(e);
    document.getElementById('matches').innerHTML = '<p class="text-red-400">Error loading data.</p>';
  }
}

loadPredictions();
