// ====================================================================
// [BLOCO] DOCUMENT_READY
// [RESPONSABILIDADE] Inicializar tela de indicadores
// ====================================================================

let chartVolume = null;
let chartTempoMedio = null;
let chartPareto = null;

document.addEventListener("DOMContentLoaded", () => {
    const app = document.getElementById("indicadoresApp");

    if (!app) {
        return;
    }

    const apiUrl = app.dataset.apiUrl;
    const dataInicio = app.dataset.dataInicio;
    const dataFim = app.dataset.dataFim;

    document.getElementById("dataInicio").value = dataInicio;
    document.getElementById("dataFim").value = dataFim;

    carregarIndicadores();

    document
        .getElementById("formFiltrosIndicadores")
        .addEventListener("submit", async (event) => {
            event.preventDefault();
            await carregarIndicadores();
        });

    async function carregarIndicadores() {
        try {
            setLoading(true);

            const inicio = document.getElementById("dataInicio").value;
            const fim = document.getElementById("dataFim").value;

            const response = await fetch(
                `${apiUrl}?data_inicio=${inicio}&data_fim=${fim}`
            );

            const payload = await response.json();

            if (!response.ok || !payload.ok) {
                throw new Error(
                    payload.mensagem || "Falha ao carregar indicadores."
                );
            }

            atualizarKPIs(payload);
            preencherVolume(payload.volume);
            preencherTempoMedio(payload.tempo_medio);
            preencherAlarmes(payload.alarmes_componentes);
            preencherOciosidade(payload.ociosidade);

        } catch (error) {
            console.error(error);

            alert(
                error.message ||
                "Falha ao consultar indicadores."
            );
        } finally {
            setLoading(false);
        }
    }
});

// ====================================================================
// [BLOCO] KPI
// ====================================================================

function atualizarKPIs(payload) {
    const resumo = payload.resumo || {};

    document.getElementById("kpiFinalizadas").textContent =
        resumo.maquinas_finalizadas ?? 0;

    document.getElementById("kpiTempoMedio").textContent =
        resumo.tempo_medio_limpo_min != null
            ? `${resumo.tempo_medio_limpo_min} min`
            : "--";

    document.getElementById("kpiAnomalias").textContent =
        resumo.anomalias_processo ?? 0;

    document.getElementById("kpiDiasProdutivos").textContent =
        resumo.dias_produtivos ?? 0;

    document.getElementById("kpiDiasOciosos").textContent =
        resumo.dias_ociosos ?? 0;
}

// ====================================================================
// [BLOCO] VOLUME
// ====================================================================

function preencherVolume(volume) {
    const tbody = document.getElementById("tbodyVolume");
    tbody.innerHTML = "";

    (volume.rows || []).forEach((row) => {
        tbody.insertAdjacentHTML(
            "beforeend",
            `
            <tr>
                <td>${row.mes_ref}</td>
                <td>${row.PM2100 ?? 0}</td>
                <td>${row.PM2200 ?? 0}</td>
                <td>${row.PM700 ?? 0}</td>
                <td><strong>${row.total ?? 0}</strong></td>
            </tr>
            `
        );
    });

    document.getElementById("statusVolume").textContent =
        `${volume.rows.length} período(s)`;

    renderChartVolume(volume);
}

function renderChartVolume(volume) {
    const ctx = document.getElementById("chartVolume");

    if (chartVolume) {
        chartVolume.destroy();
    }

    const cores = {
        PM2100: "#1f77b4",
        PM2200: "#2ca02c",
        PM700: "#ff7f0e",
    };

    chartVolume = new Chart(ctx, {
        type: "bar",
        data: {
            labels: volume.labels || [],
            datasets: (volume.datasets || []).map((item) => ({
                label: item.label,
                data: item.data,
                backgroundColor: cores[item.label] || "#999",
            })),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                },
            },
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                },
            },
        },
    });
}

// ====================================================================
// [BLOCO] TEMPO MÉDIO
// ====================================================================

function preencherTempoMedio(tempo) {
    const tbody = document.getElementById("tbodyTempoMedio");
    tbody.innerHTML = "";

    (tempo.rows || []).forEach((row) => {
        tbody.insertAdjacentHTML(
            "beforeend",
            `
            <tr>
                <td>${row.mes_ref}</td>
                <td>${formatNumber(row.PM2100)}</td>
                <td>${formatNumber(row.PM2200)}</td>
                <td>${formatNumber(row.PM700)}</td>
            </tr>
            `
        );
    });

    document.getElementById("statusTempoMedio").textContent =
        `${(tempo.anomalias || []).length} anomalia(s) filtrada(s)`;

    renderChartTempoMedio(tempo);
}

function renderChartTempoMedio(tempo) {
    const ctx = document.getElementById("chartTempoMedio");

    if (chartTempoMedio) {
        chartTempoMedio.destroy();
    }

    const cores = {
        PM2100: "#1f77b4",
        PM2200: "#2ca02c",
        PM700: "#ff7f0e",
    };

    chartTempoMedio = new Chart(ctx, {
        type: "line",
        data: {
            labels: tempo.labels || [],
            datasets: (tempo.datasets || []).map((item) => ({
                label: item.label,
                data: item.data,
                borderColor: cores[item.label] || "#999",
                backgroundColor: cores[item.label] || "#999",
                tension: 0.25,
            })),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                },
            },
        },
    });
}

// ====================================================================
// [BLOCO] ALARMES
// ====================================================================

function preencherAlarmes(alarmes) {
    const tbody = document.getElementById("tbodyAlarmes");
    tbody.innerHTML = "";

    if (!alarmes.disponivel) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7">
                    ${alarmes.mensagem || "Dados indisponíveis"}
                </td>
            </tr>
        `;

        return;
    }

    (alarmes.historico || []).forEach((item) => {
        tbody.insertAdjacentHTML(
            "beforeend",
            `
            <tr>
                <td>${item.occurred_at ?? ""}</td>
                <td>${item.bench_id ?? ""}</td>
                <td>${item.modelo ?? ""}</td>
                <td>${item.component_label ?? ""}</td>
                <td>${item.serial ?? ""}</td>
                <td>${item.downtime_min ?? ""}</td>
                <td>${item.status ?? ""}</td>
            </tr>
            `
        );
    });

    document.getElementById("statusAlarmes").textContent =
        `${(alarmes.historico || []).length} ocorrência(s)`;

    renderPareto(alarmes.pareto || []);
}

function renderPareto(pareto) {
    const ctx = document.getElementById("chartParetoAlarmes");

    if (chartPareto) {
        chartPareto.destroy();
    }

    chartPareto = new Chart(ctx, {
        type: "bar",
        data: {
            labels: pareto.map((x) => x.component_label),
            datasets: [
                {
                    label: "Downtime (min)",
                    data: pareto.map((x) => x.downtime_min),
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                },
            },
        },
    });
}

// ====================================================================
// [BLOCO] OCIOSIDADE
// ====================================================================

function preencherOciosidade(ociosidade) {
    const tbody = document.getElementById("tbodyOciosidade");
    tbody.innerHTML = "";

    tbody.insertAdjacentHTML(
        "beforeend",
        `
        <tr>
            <td>Dias Produtivos</td>
            <td>${ociosidade.dias_produtivos}</td>
        </tr>
        <tr>
            <td>Dias Ociosos</td>
            <td>${ociosidade.dias_ociosos}</td>
        </tr>
        <tr>
            <td>Taxa de Ociosidade</td>
            <td>${ociosidade.taxa_ociosidade_pct}%</td>
        </tr>
        `
    );

    (ociosidade.dias_sem_montagem || []).forEach((dia) => {
        tbody.insertAdjacentHTML(
            "beforeend",
            `
            <tr>
                <td>${dia.dia}</td>
                <td>${dia.weekday}</td>
            </tr>
            `
        );
    });

    document.getElementById("statusOciosidade").textContent =
        `${ociosidade.dias_ociosos} dia(s) sem montagem`;
}

// ====================================================================
// [BLOCO] UTIL
// ====================================================================

function setLoading(status) {
    const btn = document.getElementById("btnAplicarFiltros");

    if (!btn) {
        return;
    }

    btn.disabled = status;
    btn.textContent = status ? "Carregando..." : "Aplicar";
}

function formatNumber(value) {
    if (value == null) {
        return "--";
    }

    return Number(value).toFixed(2);
}