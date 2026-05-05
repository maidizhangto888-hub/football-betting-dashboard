function showDetailModal(match) {
  const modal = document.getElementById('modal');
  const header = document.getElementById('modal-header');
  const content = document.getElementById('modal-content');

  header.innerHTML = `${match.home_team} <span class="text-emerald-400">vs</span> ${match.away_team} <span class="text-sm text-gray-400 ml-4">${match.date} • ${match.league}</span>`;

  const h2hHtml = match.details && match.details.h2h && match.details.h2h.length > 0 
    ? match.details.h2h.map(m => `
        <div class="bg-gray-800 p-4 rounded-2xl text-center">
          <div class="text-xs text-gray-400">${m.date}</div>
          <div>${m.home} ${m.score} ${m.away}</div>
        </div>`).join('')
    : '<div class="bg-gray-800 p-8 rounded-2xl text-center text-gray-400">No recent H2H found in loaded data.<br>This is common for some fixtures early in the season.</div>';

  const homeFormHtml = match.details && match.details.home_form && match.details.home_form.length > 0 
    ? match.details.home_form.map(f => `
        <div class="bg-gray-800 p-4 rounded-2xl flex justify-between">
          <span>${f.opponent}</span>
          <span class="font-mono">${f.score}</span>
        </div>`).join('')
    : '<div class="text-gray-400 p-6">Recent home form data limited.</div>';

  const awayFormHtml = match.details && match.details.away_form && match.details.away_form.length > 0 
    ? match.details.away_form.map(f => `
        <div class="bg-gray-800 p-4 rounded-2xl flex justify-between">
          <span>${f.opponent}</span>
          <span class="font-mono">${f.score}</span>
        </div>`).join('')
    : '<div class="text-gray-400 p-6">Recent away form data limited.</div>';

  const html = `
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div>
        <h3 class="font-semibold mb-4">xG Preview</h3>
        <div class="bg-gray-800 p-6 rounded-2xl space-y-4">
          <div class="flex justify-between"><span>Home xG</span><span class="font-mono text-2xl text-emerald-400">${match.home_xg}</span></div>
          <div class="flex justify-between"><span>Away xG</span><span class="font-mono text-2xl">${match.away_xg}</span></div>
          <div class="pt-4 border-t border-gray-700 grid grid-cols-3 text-center">
            <div class="text-emerald-400 font-bold">${(match.home_win_prob*100).toFixed(0)}% HOME</div>
            <div class="font-bold">${(match.draw_prob*100).toFixed(0)}% DRAW</div>
            <div class="text-red-400 font-bold">${(match.away_win_prob*100).toFixed(0)}% AWAY</div>
          </div>
        </div>
      </div>
      <div>
        <h3 class="font-semibold mb-4">Value Bets</h3>
        <div class="space-y-3">
          ${(match.value_home || 0) > 0 ? `<div class="bg-emerald-500 text-black p-5 rounded-2xl font-semibold">HOME +${(match.value_home*100).toFixed(1)}% EDGE</div>` : ''}
          ${(match.value_draw || 0) > 0 ? `<div class="bg-emerald-500 text-black p-5 rounded-2xl font-semibold">DRAW +${(match.value_draw*100).toFixed(1)}% EDGE</div>` : ''}
          ${(match.value_away || 0) > 0 ? `<div class="bg-emerald-500 text-black p-5 rounded-2xl font-semibold">AWAY +${(match.value_away*100).toFixed(1)}% EDGE</div>` : ''}
        </div>
      </div>
    </div>

    <div class="mt-12">
      <h3 class="font-semibold mb-4">Head-to-Head (recent)</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">${h2hHtml}</div>
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

// --- 以下是新增的加载逻辑，粘贴在第76行之后 ---

// 页面加载完成后自动运行
document.addEventListener('DOMContentLoaded', () => {
    fetchData();
});

async function fetchData() {
    try {
        // 信号追踪：确保路径指向 data 文件夹下的 predictions.json
        const response = await fetch('data/predictions.json');
        if (!response.ok) throw new Error('数据文件读取失败');
        
        const data = await response.json();
        renderMatches(data);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('matches').innerHTML = `<p class="text-red-500">无法加载比赛数据，请检查后端路径。</p>`;
    }
}

function renderMatches(data) {
    const matchesContainer = document.getElementById('matches');
    matchesContainer.innerHTML = ''; // 清空加载状态

    if (!data || data.length === 0) {
        matchesContainer.innerHTML = '<p class="text-center">当前暂无预测数据</p>';
        return;
    }

    data.forEach(match => {
        const div = document.createElement('div');
        // 使用 Tailwind CSS 样式，保持与你的 index.html 设计一致
        div.className = "bg-gray-800 p-6 rounded-2xl border border-gray-700 hover:border-emerald-500 transition-all cursor-pointer mb-4";
        
        // 这里的字段名（如 home_team）需与你 predictions.json 里的 key 保持一致
        div.innerHTML = `
            <div class="flex justify-between items-center">
                <div>
                    <span class="text-lg font-bold">${match.home_team}</span>
                    <span class="text-gray-500 mx-2">vs</span>
                    <span class="text-lg font-bold">${match.away_team}</span>
                </div>
                <div class="text-right">
                    <div class="text-emerald-400 font-mono font-bold">${match.prediction || 'N/A'}</div>
                    <div class="text-xs text-gray-500">${match.league || ''}</div>
                </div>
            </div>
        `;
        
        // 绑定你原有的弹窗函数
        div.onclick = () => showDetailModal(match);
        
        matchesContainer.appendChild(div);
    });
}

// 补充：确保关闭弹窗的函数也存在
function closeModal() {
    document.getElementById('modal').classList.add('hidden');
}
