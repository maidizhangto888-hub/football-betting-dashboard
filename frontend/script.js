async function loadPredictions() {
  try {
    const response = await fetch('https://raw.githubusercontent.com/YOURUSERNAME/football-betting-dashboard/main/data/predictions.json');
    const matches = await response.json();
    
    const container = document.getElementById('matches');
    container.innerHTML = '';

    matches.forEach(match => {
      const hasValue = match.value_home > 0 || match.value_draw > 0 || match.value_away > 0;
      
      const card = document.createElement('div');
      card.className = `bg-gray-900 rounded-2xl p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 ${hasValue ? 'border border-emerald-500' : ''}`;
      
      card.innerHTML = `
        <div>
          <div class="text-xl font-semibold">${match.home_team} vs ${match.away_team}</div>
          <div class="text-sm text-gray-400">${match.date}</div>
        </div>
        
        <div class="grid grid-cols-3 gap-6 text-center">
          <div>
            <div class="text-xs text-gray-400">HOME</div>
            <div class="text-3xl font-bold">${(match.home_win_prob * 100).toFixed(0)}%</div>
            <div class="text-sm">${match.home_odds.toFixed(2)}</div>
            ${match.value_home > 0 ? `<div class="value-positive text-xs px-3 py-1 rounded-full inline-block mt-1">+${(match.value_home * 100).toFixed(1)}% EDGE</div>` : ''}
          </div>
          <div>
            <div class="text-xs text-gray-400">DRAW</div>
            <div class="text-3xl font-bold">${(match.draw_prob * 100).toFixed(0)}%</div>
            <div class="text-sm">${match.draw_odds.toFixed(2)}</div>
            ${match.value_draw > 0 ? `<div class="value-positive text-xs px-3 py-1 rounded-full inline-block mt-1">+${(match.value_draw * 100).toFixed(1)}% EDGE</div>` : ''}
          </div>
          <div>
            <div class="text-xs text-gray-400">AWAY</div>
            <div class="text-3xl font-bold">${(match.away_win_prob * 100).toFixed(0)}%</div>
            <div class="text-sm">${match.away_odds.toFixed(2)}</div>
            ${match.value_away > 0 ? `<div class="value-positive text-xs px-3 py-1 rounded-full inline-block mt-1">+${(match.value_away * 100).toFixed(1)}% EDGE</div>` : ''}
          </div>
        </div>
      `;
      container.appendChild(card);
    });
    
    if (matches.length === 0) {
      container.innerHTML = '<p class="text-gray-400 text-center py-12">No upcoming matches at the moment.</p>';
    }
  } catch (e) {
    console.error(e);
    document.getElementById('matches').innerHTML = '<p class="text-red-400">Error loading data. Make sure the GitHub Action has run at least once.</p>';
  }
}

loadPredictions();
