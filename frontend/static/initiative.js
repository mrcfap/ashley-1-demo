(() => {
  const panel = document.getElementById('initiativePanel');
  const status = document.getElementById('initiativeStatus');
  const initiative = '/api/v1/iniciativa';
  const suggestions = '/api/v1/engines/v96';

  async function request(path, body) {
    const token = sessionStorage.getItem('ashley_token') || localStorage.getItem('ashley_token');
    if (!token) throw new Error('Entre na conta para acessar os registros.');
    const response = await fetch(path, {
      method: body === undefined ? 'GET' : 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!response.ok) throw new Error('A solicitação falhou (HTTP ' + response.status + ').');
    return response.json();
  }

  function render(id, entries, describe) {
    const list = document.getElementById(id);
    list.replaceChildren();
    for (const entry of entries) {
      const item = document.createElement('li');
      item.textContent = describe(entry);
      list.append(item);
    }
  }

  async function refresh() {
    const [turns, alerts, result] = await Promise.all([
      request(initiative + '/turnos'),
      request(initiative + '/alertas'),
      request(suggestions + '/proposals'),
    ]);
    render('shiftList', turns, row => new Date(row.created).toLocaleString() + ' — ' + row.resumo);
    render('alertList', alerts, row => row.titulo + ' — ' + row.descricao + ' (prioridade ' + row.prioridade + ')');
    render('suggestionList', result.proposals, row => row.suggested_action + ' — ' + row.context);
    for (const [index, row] of result.proposals.entries()) {
      if (row.status !== 'pending') continue;
      const item = document.getElementById('suggestionList').children[index];
      for (const approved of [true, false]) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'action';
        button.textContent = approved ? 'Aprovar para ação manual' : 'Rejeitar';
        button.onclick = () => run(async () => {
          await request(suggestions + '/proposals/' + encodeURIComponent(row.id) + '/review?approved=' + approved, {});
          await refresh();
        });
        item.append(' ', button);
      }
    }
  }

  let busy = false;
  async function run(operation) {
    if (busy) return;
    busy = true;
    status.textContent = '';
    try {
      await operation();
    } catch (error) {
      status.textContent = error.message;
    } finally {
      busy = false;
    }
  }

  function bind(id, path, encode = data => data) {
    const form = document.getElementById(id);
    form.addEventListener('submit', event => {
      event.preventDefault();
      run(async () => {
        await request(path, encode(Object.fromEntries(new FormData(form))));
        form.reset();
        try {
          await refresh();
          status.textContent = 'Registro salvo.';
        } catch {
          status.textContent = 'Registro salvo. Use Atualizar registros para recarregar a lista.';
        }
      });
    });
  }

  bind('shiftEntry', initiative + '/turnos');
  bind('alertEntry', initiative + '/alertas', data => ({ ...data, prioridade: Number(data.prioridade) }));
  bind('suggestionEntry', suggestions + '/proactive/trigger', data => ({ data: { ...data, consent: data.consent === 'on' } }));
  document.getElementById('initiativeRefresh').onclick = () => run(refresh);
  panel.addEventListener('toggle', () => { if (panel.open) run(refresh); });
})();
