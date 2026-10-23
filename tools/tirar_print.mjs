// Abre a exportacao HTML5 do jogo num navegador sem tela, vai ate uma cena e
// salva um print. Serve para conferir visualmente mudancas de interface e de
// tipografia, que o comparador de codigo nao enxerga.
//
//   npx gdexporter@4.0.0-beta7 -p ProjetoGameDEv4.json -o build
//   node tools/tirar_print.mjs build saida.png quiz_game 8
//
// Argumentos: <build> <arquivo.png> [cena|-] [segundos de espera apos trocar]
//
// O Playwright vem do ambiente, em /opt/node-tools, que e onde estao os
// navegadores ja baixados.

import pw from '/opt/node-tools/node_modules/playwright/index.js';
const { chromium } = pw;
const [,, dir, saida, cena, segundos] = process.argv;
const http = await import('node:http');
const fs = await import('node:fs');
const path = await import('node:path');
const tipos = {'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png',
  '.jpg':'image/jpeg','.wav':'audio/wav','.mp3':'audio/mpeg','.ttf':'font/ttf','.glb':'model/gltf-binary'};
const srv = http.createServer((req,res)=>{
  const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\//,'') || 'index.html';
  const p = path.join(dir, rel);
  fs.readFile(p,(e,d)=> {
    if (e) { res.writeHead(404); return res.end(); }
    let corpo = d;
    // O jogo e criado dentro de uma IIFE, entao a instancia nao fica acessivel
    // de fora. Expo-la aqui, so no arquivo servido, deixa o teste trocar de
    // cena sem precisar jogar a fase inteira. O repositorio nao e tocado.
    if (rel === 'index.html') {
      corpo = Buffer.from(d.toString('utf-8').replace(
        'var game = new gdjs.RuntimeGame(gdjs.projectData, {});',
        'var game = new gdjs.RuntimeGame(gdjs.projectData, {}); window.__game = game;'), 'utf-8');
    }
    res.writeHead(200,{'Content-Type':tipos[path.extname(p)]||'application/octet-stream'});
    res.end(corpo);
  });
});
await new Promise(r=>srv.listen(0,r));
const porta = srv.address().port;
const b = await chromium.launch({args:['--autoplay-policy=no-user-gesture-required','--mute-audio']});
const pg = await b.newPage({viewport:{width:1920,height:1080}});
const erros=[];
pg.on('console', m => m.type()==='error' && erros.push(m.text()));
pg.on('pageerror', e => erros.push('PAGEERROR: '+e.message));
await pg.goto(`http://127.0.0.1:${porta}/index.html`, {waitUntil:'domcontentloaded', timeout:60000});
await pg.waitForTimeout(20000);
if (cena && cena !== '-') {
  const ok = await pg.evaluate(c => {
    const g = window.__game;
    if (!g || !g.getSceneStack) return 'sem acesso ao jogo';
    g.getSceneStack().replace(c, true);
    return true;
  }, cena);
  if (ok !== true) { console.log('ERRO troca de cena:', ok); }
  await pg.waitForTimeout(Number(segundos||5)*1000);
}
const atual = await pg.evaluate(() => {
  const g = window.__game; if (!g || !g.getSceneStack) return '?';
  const c = g.getSceneStack().getCurrentScene();
  return c ? c.getName() : '(nenhuma)';
});
console.log('cena em tela:', atual);
await pg.screenshot({path: saida});
console.log('print salvo:', saida);
console.log('erros de console:', erros.length);
erros.slice(0,8).forEach(e=>console.log('  ', e.slice(0,160)));
await b.close(); srv.close();
