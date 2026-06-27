let perfilSelecionado = "aluno";
let usuarioAtual = null;


function mudarTema(tema) {
    document.body.className = "";
    document.body.classList.add(tema);
}


async function buscarJson(url, opcoes = {}) {
    const resposta = await fetch(url, opcoes);
    const corpo = await resposta.json();
    if (!resposta.ok) {
        throw new Error(corpo.erro || "Nao foi possivel concluir a operacao.");
    }
    return corpo;
}


function configurarAbas() {
    document.querySelectorAll(".aba").forEach(botao => {
        botao.addEventListener("click", () => {
            perfilSelecionado = botao.dataset.perfil;
            document.querySelectorAll(".aba").forEach(item => item.classList.remove("ativa"));
            botao.classList.add("ativa");
            atualizarFormulario();
            carregarExemplos();
        });
    });
}


function atualizarFormulario() {
    const aluno = perfilSelecionado === "aluno";
    document.getElementById("titulo-formulario").textContent = aluno ? "Cadastrar aluno" : "Cadastrar professor";
    document.getElementById("botao-cadastro").textContent = aluno ? "Cadastrar aluno" : "Cadastrar professor";
    document.getElementById("campo-aluno").hidden = !aluno;
    document.getElementById("campo-professor").hidden = aluno;
    document.getElementById("turma").required = aluno;
    document.getElementById("disciplina").required = !aluno;
}


function criarBotaoExemplo(usuario) {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "item-exemplo";
    botao.innerHTML = `
        <strong>${usuario.nome}</strong>
        <span>${perfilSelecionado === "aluno" ? usuario.turma : usuario.disciplina}</span>
        <small>${usuario.email}</small>
    `;
    botao.addEventListener("click", () => abrirDashboard(perfilSelecionado, usuario.id));
    return botao;
}


async function carregarExemplos() {
    const lista = document.getElementById("lista-exemplos");
    lista.innerHTML = "<p>Carregando cadastros...</p>";

    try {
        const endpoint = perfilSelecionado === "aluno" ? "/api/alunos" : "/api/professores";
        const usuarios = await buscarJson(endpoint);
        lista.innerHTML = "";
        usuarios.forEach(usuario => lista.appendChild(criarBotaoExemplo(usuario)));
    } catch (erro) {
        lista.innerHTML = `<p class="erro">${erro.message}</p>`;
    }
}


function configurarCadastro() {
    const form = document.getElementById("form-cadastro");
    form.addEventListener("submit", async event => {
        event.preventDefault();

        const dados = Object.fromEntries(new FormData(form));
        const endpoint = perfilSelecionado === "aluno" ? "/api/alunos" : "/api/professores";

        try {
            const usuario = await buscarJson(endpoint, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(dados),
            });
            form.reset();
            await carregarExemplos();
            await abrirDashboard(perfilSelecionado, usuario.id);
        } catch (erro) {
            alert(erro.message);
        }
    });
}


function detalhePerfil(perfil, pessoa) {
    if (perfil === "aluno") {
        return `${pessoa.turma} | Objetivo: ${pessoa.objetivo}`;
    }
    return `${pessoa.disciplina} | Especialidade: ${pessoa.especialidade}`;
}


async function abrirDashboard(perfil, id) {
    usuarioAtual = {perfil, id};
    const dados = await buscarJson(`/api/microlearning/${perfil}/${id}`);

    document.getElementById("dashboard").hidden = false;
    document.getElementById("perfil-atual").textContent = perfil === "aluno" ? "Area do aluno" : "Area do professor";
    document.getElementById("texto-saudacao").textContent = dados.saudacao;
    document.getElementById("detalhe-perfil").textContent = detalhePerfil(perfil, dados.pessoa);

    if (perfil === "aluno") {
        renderizarAluno(dados);
    } else {
        renderizarProfessor(dados);
    }

    document.getElementById("dashboard").scrollIntoView({behavior: "smooth", block: "start"});
}


function renderizarAluno(dados) {
    const area = document.getElementById("area-microlearning");
    const concluidas = dados.atividades.filter(item => item.concluida).length;
    const total = dados.atividades.length || 1;
    const percentual = Math.round((concluidas / total) * 100);

    area.innerHTML = `
        <article class="resumo-progresso">
            <strong>${percentual}% concluido</strong>
            <span>${concluidas} de ${dados.atividades.length} atividades finalizadas</span>
            <div class="barra"><span style="width: ${percentual}%"></span></div>
        </article>
        <div class="lista-atividades"></div>
    `;

    const lista = area.querySelector(".lista-atividades");
    dados.atividades.forEach(atividade => {
        const item = document.createElement("article");
        item.className = "atividade";
        item.innerHTML = `
            <div>
                <span class="etiqueta">${atividade.curso} | ${atividade.duracao_minutos} min</span>
                <h3>${atividade.micro_aula}</h3>
                <p>${atividade.conteudo}</p>
                <strong>${atividade.enunciado}</strong>
            </div>
            <label class="check-atividade">
                <input type="checkbox" ${atividade.concluida ? "checked" : ""}>
                <span>Concluida</span>
            </label>
        `;

        item.querySelector("input").addEventListener("change", async event => {
            await salvarProgresso(atividade.id, event.target.checked);
        });
        lista.appendChild(item);
    });
}


async function salvarProgresso(atividadeId, concluida) {
    await buscarJson("/api/progresso", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            aluno_id: usuarioAtual.id,
            atividade_id: atividadeId,
            concluida,
        }),
    });
    await abrirDashboard("aluno", usuarioAtual.id);
}


function renderizarProfessor(dados) {
    const resumo = dados.resumo_turma;
    const concluidas = resumo.concluidas || 0;
    const entregas = resumo.entregas || 0;

    document.getElementById("area-microlearning").innerHTML = `
        <div class="metricas">
            <article><strong>${resumo.alunos}</strong><span>alunos cadastrados</span></article>
            <article><strong>${entregas}</strong><span>atividades iniciadas</span></article>
            <article><strong>${concluidas}</strong><span>conclusoes registradas</span></article>
        </div>
        <div class="lista-atividades">
            ${dados.aulas.map(aula => `
                <article class="atividade">
                    <div>
                        <span class="etiqueta">${aula.curso} | ${aula.duracao_minutos} min</span>
                        <h3>${aula.micro_aula}</h3>
                        <p>${aula.conteudo}</p>
                        <strong>${aula.atividades} atividade(s) vinculada(s)</strong>
                    </div>
                </article>
            `).join("")}
        </div>
    `;
}


async function carregarResumoBanco() {
    const resumo = await buscarJson("/api/banco/resumo");
    const container = document.getElementById("resumo-banco");
    container.innerHTML = Object.entries(resumo.tabelas).map(([tabela, total]) => `
        <article>
            <strong>${total}</strong>
            <span>${tabela}</span>
        </article>
    `).join("");
}


function configurarTrocaPerfil() {
    document.getElementById("trocar-perfil").addEventListener("click", () => {
        document.querySelector(".entrada").scrollIntoView({behavior: "smooth", block: "start"});
    });
}


window.onload = async function inicializarApp() {
    configurarAbas();
    configurarCadastro();
    configurarTrocaPerfil();
    atualizarFormulario();
    await carregarExemplos();
    await carregarResumoBanco();
};
