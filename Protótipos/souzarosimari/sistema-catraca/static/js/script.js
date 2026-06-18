/**
 * Catraca Virtual — script compartilhado entre as páginas.
 *
 * Em vez de depender de arquivos de áudio externos (que podem não existir
 * ou exigir internet), os "bipes" da catraca são gerados ao vivo com a
 * Web Audio API. Isso garante que o som funcione em qualquer celular,
 * mesmo offline, sem precisar baixar nenhum arquivo .mp3/.ogg.
 */
window.CatracaApp = (function () {
    "use strict";

    function tocarSom(status) {
        try {
            var AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;
            var ctx = new AudioCtx();

            if (status === "aprovado") {
                bipe(ctx, 880, 0.0, 0.12, "sine");
                bipe(ctx, 1180, 0.13, 0.16, "sine");
            } else {
                bipe(ctx, 220, 0.0, 0.18, "square");
                bipe(ctx, 180, 0.2, 0.22, "square");
            }
        } catch (erro) {
            // Alguns navegadores bloqueiam áudio sem interação do usuário;
            // nesse caso o sistema simplesmente segue em silêncio.
            console.warn("Não foi possível reproduzir o som da catraca:", erro);
        }
    }

    function bipe(ctx, frequencia, inicio, duracao, tipo) {
        var oscilador = ctx.createOscillator();
        var ganho = ctx.createGain();

        oscilador.type = tipo;
        oscilador.frequency.value = frequencia;

        ganho.gain.setValueAtTime(0.0001, ctx.currentTime + inicio);
        ganho.gain.exponentialRampToValueAtTime(0.22, ctx.currentTime + inicio + 0.02);
        ganho.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + inicio + duracao);

        oscilador.connect(ganho);
        ganho.connect(ctx.destination);

        oscilador.start(ctx.currentTime + inicio);
        oscilador.stop(ctx.currentTime + inicio + duracao + 0.02);
    }

    /**
     * Conta de `segundos` até 0 atualizando o elemento `elementoId`.
     * Ao chegar a zero: redireciona para `destino` (se informado) ou
     * recarrega a própria página (usado no histórico).
     */
    function iniciarContagemRegressiva(elementoId, segundos, destino, recarregar) {
        var alvo = document.getElementById(elementoId);
        if (!alvo) return;

        var restante = segundos;
        alvo.textContent = restante;

        var intervalo = setInterval(function () {
            restante -= 1;
            if (restante <= 0) {
                clearInterval(intervalo);
                if (recarregar) {
                    window.location.reload();
                } else if (destino) {
                    window.location.href = destino;
                }
                return;
            }
            alvo.textContent = restante;
        }, 1000);
    }

    return {
        tocarSom: tocarSom,
        iniciarContagemRegressiva: iniciarContagemRegressiva
    };
})();
