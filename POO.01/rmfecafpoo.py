"""
Sistema de Orçamento de Aluguel - Imobiliária R.M
--------------------------------------------------
Programa em Python 3, orientado a objetos, que calcula o orçamento
mensal de aluguel para três tipos de imóvel (Apartamento, Casa e
Estúdio), calcula o valor da parcela do contrato imobiliário e gera
um arquivo .csv com a projeção do aluguel ao longo de 12 meses.

Este código foi pensado para fins didáticos (estudante iniciante em
programação), por isso os comentários explicam cada parte da lógica.

CORREÇÕES APLICADAS APÓS BATERIA DE TESTES:
  1. Tratamento de EOFError/KeyboardInterrupt nas funções de entrada,
     evitando que o programa quebre com traceback se a entrada de
     dados for interrompida.
  2. Cálculo das parcelas do contrato com precisão decimal (usando o
     módulo `decimal`), ajustando a última parcela para que a soma
     das parcelas seja sempre igual ao valor total do contrato (sem
     "sobra" de centavos por arredondamento).
  3. Formatação monetária no padrão brasileiro (vírgula como separador
     decimal), tanto na tela quanto no arquivo .csv gerado.
"""

import csv
import sys
from decimal import Decimal, ROUND_HALF_UP
""" 
Importa a classe Decimal e a regra de arredondamento ROUND_HALF_UP.
"""

def formatar_moeda(valor) -> str:
    """
    Formata um número (float ou Decimal) no padrão monetário brasileiro,
    com vírgula como separador decimal (ex.: 1234.5 -> "1.234,50").
    """
    texto = f"{float(valor):,.2f}"          # formato "en_US": 1,234.50
    texto = texto.replace(",", "X")          # protege o separador de milhar
    texto = texto.replace(".", ",")          # decimal americano -> vírgula BR
    texto = texto.replace("X", ".")          # milhar americano -> ponto BR
    return texto


# ---------------------------------------------------------------------------
# CLASSE BASE (superclasse)
# ---------------------------------------------------------------------------

class Imovel:
    """
    Classe base que representa um imóvel genérico.
    As subclasses (Apartamento, Casa, Estudio) herdam desta classe e
    sobrescrevem o método calcular_aluguel() com suas próprias regras
    de negócio (polimorfismo).
    """

    def __init__(self, quartos: int, valor_base: float):
        # Atributos "protegidos" (convenção com um underscore) para
        # simular encapsulamento em Python.
        self._quartos = quartos
        self._valor_base = valor_base

    # --- getters simples (encapsulamento) ---
    def get_quartos(self) -> int:
        return self._quartos

    def get_valor_base(self) -> float:
        return self._valor_base

    def calcular_aluguel(self) -> float:
        """
        Método padrão. Cada subclasse deve sobrescrever este método
        com sua própria regra de cálculo.
        """
        return self._valor_base


# ---------------------------------------------------------------------------
# SUBCLASSE: APARTAMENTO
# ---------------------------------------------------------------------------
class Apartamento(Imovel):
    """
    Regras do Apartamento:
      - Valor base: R$ 700,00 (1 quarto)
      - 2 quartos: + R$ 200,00
      - Garagem (opcional): + R$ 300,00
      - Desconto de 5% se o cliente não possuir crianças
    """

    VALOR_BASE = 700.00
    ACRESCIMO_2_QUARTOS = 200.00
    VALOR_GARAGEM = 300.00
    DESCONTO_SEM_CRIANCAS = 0.05  # 5%

    def __init__(self, quartos: int, garagem: bool, tem_criancas: bool):
        super().__init__(quartos, self.VALOR_BASE)
        self._garagem = garagem
        self._tem_criancas = tem_criancas

    def calcular_aluguel(self) -> float:
        valor = self._valor_base

        # Regra: apartamento com 2 quartos recebe acréscimo fixo
        if self._quartos == 2:
            valor += self.ACRESCIMO_2_QUARTOS

        # Regra: vaga de garagem opcional
        if self._garagem:
            valor += self.VALOR_GARAGEM

        # Regra: desconto de 5% apenas para quem não tem crianças
        if not self._tem_criancas:
            valor -= valor * self.DESCONTO_SEM_CRIANCAS

        return valor


# ---------------------------------------------------------------------------
# SUBCLASSE: CASA
# ---------------------------------------------------------------------------
class Casa(Imovel):
    """
    Regras da Casa:
      - Valor base: R$ 900,00 (1 quarto)
      - 2 quartos: + R$ 250,00
      - Garagem (opcional): + R$ 300,00
    """

    VALOR_BASE = 900.00
    ACRESCIMO_2_QUARTOS = 250.00
    VALOR_GARAGEM = 300.00

    def __init__(self, quartos: int, garagem: bool):
        super().__init__(quartos, self.VALOR_BASE)
        self._garagem = garagem

    def calcular_aluguel(self) -> float:
        valor = self._valor_base

        # Regra: casa com 2 quartos recebe acréscimo fixo
        if self._quartos == 2:
            valor += self.ACRESCIMO_2_QUARTOS

        # Regra: vaga de garagem opcional
        if self._garagem:
            valor += self.VALOR_GARAGEM

        return valor


# ---------------------------------------------------------------------------
# SUBCLASSE: ESTUDIO
# ---------------------------------------------------------------------------
class Estudio(Imovel):
    """
    Regras do Estúdio:
      - Valor fixo: R$ 1.200,00 (não varia por número de quartos)
      - Vagas de estacionamento:
          * Pacote de 2 vagas por R$ 250,00 (fixo)
          * Cada vaga extra (além das 2 do pacote): + R$ 60,00
    """

    VALOR_BASE = 1200.00
    VALOR_PACOTE_2_VAGAS = 250.00
    VALOR_VAGA_EXTRA = 60.00
    VAGAS_INCLUSAS_NO_PACOTE = 2

    def __init__(self, vagas_estacionamento: int = 0):
        # Estúdio não possui variação por quartos, então não usamos
        # o parâmetro "quartos" da classe base (fica fixo em 0/None).
        super().__init__(quartos=0, valor_base=self.VALOR_BASE)
        self._vagas_estacionamento = vagas_estacionamento

    def calcular_aluguel(self) -> float:
        valor = self._valor_base

        if self._vagas_estacionamento > 0:
            # Cobra o pacote fixo de 2 vagas
            valor += self.VALOR_PACOTE_2_VAGAS

            # Cobra vagas extras além das 2 inclusas no pacote
            vagas_extras = max(
                0, self._vagas_estacionamento - self.VAGAS_INCLUSAS_NO_PACOTE
            )
            valor += vagas_extras * self.VALOR_VAGA_EXTRA

        return valor


# ---------------------------------------------------------------------------
# CLASSE: CONTRATO
# ---------------------------------------------------------------------------
class Contrato:
    """
    Representa o contrato imobiliário, com valor fixo de R$ 2.000,00,
    que pode ser parcelado em até 5 vezes.

    Observação técnica: o valor total é dividido usando o módulo
    `decimal`, e a ÚLTIMA parcela é ajustada para absorver eventuais
    centavos de arredondamento. Isso evita o problema clássico de
    "drift" de arredondamento (ex.: R$ 2000,00 / 3 = R$ 666,666... ;
    se todas as parcelas fossem simplesmente arredondadas para
    R$ 666,67, a soma ficaria em R$ 2000,01, um centavo a mais do
    que o valor real do contrato).
    """

    VALOR_TOTAL = Decimal("2000.00")
    MAX_PARCELAS = 5

    def __init__(self, numero_parcelas: int):
        if not (1 <= numero_parcelas <= self.MAX_PARCELAS):
            raise ValueError("O número de parcelas deve ser entre 1 e 5.")
        self._numero_parcelas = numero_parcelas

    def calcular_parcelas(self) -> list:
        """
        Retorna uma lista com o valor (Decimal) de cada parcela.
        Todas as parcelas têm o mesmo valor, exceto a última, que
        absorve a diferença de centavos do arredondamento — garantindo
        que a soma das parcelas seja sempre EXATAMENTE igual ao valor
        total do contrato.
        """
        n = self._numero_parcelas
        centavos = Decimal("0.01")

        valor_parcela = (self.VALOR_TOTAL / n).quantize(
            centavos, rounding=ROUND_HALF_UP
        )

        parcelas = [valor_parcela] * (n - 1)
        soma_parcial = valor_parcela * (n - 1)
        ultima_parcela = (self.VALOR_TOTAL - soma_parcial).quantize(
            centavos, rounding=ROUND_HALF_UP
        )
        parcelas.append(ultima_parcela)

        return parcelas

    def calcular_valor_parcela(self) -> Decimal:
        """Mantido por compatibilidade: retorna o valor da 1ª parcela."""
        return self.calcular_parcelas()[0]

    def get_numero_parcelas(self) -> int:
        return self._numero_parcelas


# ---------------------------------------------------------------------------
# CLASSE: ORCAMENTO (une Imovel + Contrato)
# ---------------------------------------------------------------------------
class Orcamento:
    """
    Classe responsável por unir o imóvel escolhido e o contrato,
    calcular o valor final do orçamento e gerar o arquivo .csv com a
    projeção das 12 parcelas mensais do aluguel.
    """

    MESES_PROJECAO = 12

    def __init__(self, imovel: Imovel, contrato: Contrato):
        self._imovel = imovel
        self._contrato = contrato

    def calcular_aluguel_mensal(self) -> float:
        return self._imovel.calcular_aluguel()

    def calcular_valor_parcela_contrato(self) -> Decimal:
        return self._contrato.calcular_valor_parcela()

    def exibir_resumo(self, tipo_imovel: str) -> None:
        """Exibe na tela o resumo do orçamento calculado."""
        aluguel_mensal = self.calcular_aluguel_mensal()
        parcelas = self._contrato.calcular_parcelas()
        numero_parcelas = self._contrato.get_numero_parcelas()

        print("\n===== RESUMO DO ORÇAMENTO =====")
        print(f"Tipo de imóvel: {tipo_imovel}")
        print(f"Valor do aluguel mensal: R$ {formatar_moeda(aluguel_mensal)}")
        print(f"Valor do contrato: R$ {formatar_moeda(Contrato.VALOR_TOTAL)}")

        # Se todas as parcelas tiverem o mesmo valor, mostra de forma resumida.
        # Caso a última parcela tenha sido ajustada (centavos), mostra o detalhe.
        if len(set(parcelas)) == 1:
            print(
                f"Parcelado em: {numero_parcelas}x de R$ {formatar_moeda(parcelas[0])}"
            )
        else:
            valores = " + ".join(
                f"{i + 1}ª: R$ {formatar_moeda(p)}" for i, p in enumerate(parcelas)
            )
            print(f"Parcelado em {numero_parcelas}x -> {valores}")
        print("================================\n")

    def gerar_csv(self, nome_arquivo: str = "orcamento_aluguel.csv") -> None:
        """
        Gera um arquivo .csv com a projeção do aluguel ao longo de
        12 meses. Nos meses em que ainda há parcela do contrato em
        aberto, o valor da parcela correspondente também é somado ao
        total do mês.

        Usa a lista de parcelas exatas (calcular_parcelas), e não um
        valor único repetido, para que a soma das parcelas no CSV
        bata exatamente com o valor total do contrato (sem sobra de
        centavos por arredondamento). Os valores são gravados no
        formato monetário brasileiro (vírgula decimal).
        """
        aluguel_mensal = self.calcular_aluguel_mensal()
        parcelas = self._contrato.calcular_parcelas()
        numero_parcelas = self._contrato.get_numero_parcelas()

        with open(nome_arquivo, mode="w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            # Cabeçalho do arquivo
            escritor.writerow(
                ["Mes", "Valor Aluguel (R$)", "Parcela Contrato (R$)", "Total do Mes (R$)"]
            )

            for mes in range(1, self.MESES_PROJECAO + 1):
                # A parcela do contrato só é cobrada até o número de
                # parcelas escolhido pelo cliente (usa o valor exato
                # daquela parcela específica na lista, não uma média).
                if mes <= numero_parcelas:
                    parcela_do_mes = parcelas[mes - 1]
                else:
                    parcela_do_mes = Decimal("0.00")

                total_mes = Decimal(str(aluguel_mensal)) + parcela_do_mes

                escritor.writerow(
                    [
                        mes,
                        formatar_moeda(aluguel_mensal),
                        formatar_moeda(parcela_do_mes),
                        formatar_moeda(total_mes),
                    ]
                )

        print(f"Arquivo '{nome_arquivo}' gerado com sucesso!")


# ---------------------------------------------------------------------------
# FUNÇÕES AUXILIARES DE ENTRADA (validação simples de dados do usuário)
# ---------------------------------------------------------------------------
def encerrar_por_interrupcao() -> None:
    """
    Encerra o programa de forma controlada quando a entrada de dados é
    interrompida (EOF) ou o usuário cancela com Ctrl+C. Evita que um
    traceback "cru" seja exibido ao usuário final.
    """
    print("\n\nEntrada de dados interrompida. Encerrando o programa.")
    sys.exit(1)


def ler_opcao(mensagem: str, opcoes_validas: list) -> str:
    """Lê uma opção de texto do usuário e valida se está entre as opções aceitas."""
    while True:
        try:
            resposta = input(mensagem).strip().lower()
        except (EOFError, KeyboardInterrupt):
            encerrar_por_interrupcao()
        if resposta in opcoes_validas:
            return resposta
        print(f"Opção inválida. Escolha uma das opções: {opcoes_validas}")


def ler_inteiro(mensagem: str, minimo: int, maximo: int) -> int:
    """Lê um número inteiro do usuário e valida se está dentro do intervalo permitido."""
    while True:
        try:
            valor = int(input(mensagem))
        except (EOFError, KeyboardInterrupt):
            encerrar_por_interrupcao()
        except ValueError:
            print("Entrada inválida. Digite um número inteiro.")
            continue

        if minimo <= valor <= maximo:
            return valor
        print(f"Digite um número entre {minimo} e {maximo}.")


def ler_sim_nao(mensagem: str) -> bool:
    """Lê uma resposta sim/não do usuário e retorna um booleano."""
    resposta = ler_opcao(mensagem, ["s", "n"])
    return resposta == "s"


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------------------------
def main():
    print("========================================")
    print(" SISTEMA DE ORÇAMENTO DE ALUGUEL - R.M ")
    print("========================================\n")

    # 1) Escolha do tipo de imóvel
    tipo = ler_opcao(
        "Escolha o tipo de imóvel (apartamento / casa / estudio): ",
        ["apartamento", "casa", "estudio"],
    )

    imovel = None
    tipo_exibicao = ""

    if tipo == "apartamento":
        quartos = ler_inteiro("Quantos quartos (1 ou 2)? ", 1, 2)
        garagem = ler_sim_nao("Deseja incluir vaga de garagem? (s/n): ")
        tem_criancas = ler_sim_nao("O cliente possui crianças? (s/n): ")
        imovel = Apartamento(quartos, garagem, tem_criancas)
        tipo_exibicao = "Apartamento"

    elif tipo == "casa":
        quartos = ler_inteiro("Quantos quartos (1 ou 2)? ", 1, 2)
        garagem = ler_sim_nao("Deseja incluir vaga de garagem? (s/n): ")
        imovel = Casa(quartos, garagem)
        tipo_exibicao = "Casa"

    elif tipo == "estudio":
        quer_vaga = ler_sim_nao("Deseja incluir vagas de estacionamento? (s/n): ")
        vagas = 0
        if quer_vaga:
            vagas = ler_inteiro(
                "Quantas vagas no total (mínimo 2, pacote já inclui 2)? ", 2, 20
            )
        imovel = Estudio(vagas)
        tipo_exibicao = "Estúdio"

    # 2) Número de parcelas do contrato (1 a 5)
    numero_parcelas = ler_inteiro(
        "Em quantas vezes deseja parcelar o contrato (1 a 5)? ", 1, 5
    )
    contrato = Contrato(numero_parcelas)

    # 3) Monta o orçamento, exibe o resumo e gera o CSV
    orcamento = Orcamento(imovel, contrato)
    orcamento.exibir_resumo(tipo_exibicao)
    orcamento.gerar_csv("orcamento_aluguel.csv")


if __name__ == "__main__":
    main()