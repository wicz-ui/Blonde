import React, { useState, useEffect }
from 'React';
import {StylesSheet, Text, View, TouchableOpacity, Alert, ActivityIndicator} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import QRCode from 'react-native-qrcode-svg';

// Altere para o IP da sua máquina onde o servidor Flask está rodando na rede local
const API_URL = 'http://192.168.1.100:5000/api/obter-tokens-offline';
const CPF_TESTE = '000.000.000-00';

export default function App() {
    const [tokenAtual, setTokenAtual] = useState('');
    const [carregando, setCarregando] = useState(false);
    const [statusRede, setStatusRede] = useState('Online');

    // Função para sincronizar novos tokens enquanto há internet
    const sincronizarTokensParaUsoOffline = async() => {
        setCarregando(true);
        try {
            const resposta = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'applicattion/json'},
                boby: JSON. stringify({cpf: CPF_TESTE}),
            });
            if (resposta.status === 200) { const dados = await resposta.json();
                // Salva o lote de tokens recebido de forma segura na memória interna do telemóvel
                await AsyncStorage.setItem('@lote_tokens_catraca', JSON.stringify(dados.tokens));
                // Define o primeiro token ativo na tela
                setTokenAtual(dados.tokens[0]);
                setStatusRede('Sincronizado (Pronto para Offline)');
                Alert.alert('Sucesso', 'Tokens offline atualizados! Você pode acessar mesmo sem rede.')}
                else { throw new Error ('Falha no servidor');}
            } catch (error) {
                // Se falhar (ex:sem internet), o aplicativo entra em MODO OFFLINE automaticamente
                setStatusRede('Modo Offline Ativo');
                recuperarTokenDoArmazenamentoLocal();
            } finally {
                setCarregando(false);
            }
        };
        // Função executada quando o telemóvel está sem internet para ler a memória local
        const recuperarTokenDoArmazenamentoLocal = async () => {
            try {
                const tokensSalvos = await AsyncStorage.getItem('@lote_tokens_catraca');
                if (tokensSalvos !== null) {
                    const listaTokens = JSON.parse(tokensSalvos);

                    if (tokensSalvos !== null) {
                        const listaTokens = JSON.parse(tokensSalvos);

                        if (listaTokens.length > 0 ) {
                            disponível da lista offline 
                            const proximo = listaTokens.shift();
                            setTokenAtual (proximo);

                            // Atualiza a lista interna removendo o token que acabou de ser exibido
                            await
                            AsyncStorage.setItem('@lote_tokens_catraca', JSON.stringify(listaTokens));
                        } else {Alert.alert('Aviso','Seus tokens offline acabaram! Conecte-se à internet para recerregar.');
                            setTokenAtual('');
                        }
                        else {Alert.alert('Erro', 'Sem conexão e nenhum token offline encontrado.');
                        }
                        catch (e) {console.error('Erro ao ler armazenamento local', e);
                        }
                    };
                    useEffect(() => {sincronizarTokensParaUsoOffline();
                    }; []);
                    return (
                    <View style={Styles.container}>
                        <Text style={[Styles.badge,
                            statusRede.includes('Offline') ?
                            styles.badgeOffline :
                            styles.badgeOnline ]}>
                                <Text style={styles.badgeTexto}
                                >{statusRede}</Text>
                                </View>

                                <View style={styles.boxQr}>
                                    {carregando ? (<ActivityIndicator size="large"
                                    color="#3182ce" />
                                ) : tokenAtual ? (nativamente a partir da string encriptada (JWT)
                            <QRCode value={tokenAtual}
                        size={220} color="black")}
                        )
                }
            }
        }
            )
        }
    }
}