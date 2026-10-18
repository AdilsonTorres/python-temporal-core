"""Entity workflow: um carrinho = um workflow vivo, que muda por Updates."""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from .activities import registrar_pedido
    from .modelos import Carrinho, Item

OCIOSO = timedelta(days=1)


@workflow.defn
class CarrinhoWorkflow:
    def __init__(self) -> None:
        self.itens: dict[str, Item] = {}
        self.fechado = False
        self.mexeu = False

    def total_atual(self) -> float:
        return sum(i.quantidade * i.preco for i in self.itens.values())

    @workflow.run
    async def run(self, carrinho: Carrinho) -> str:
        self.itens = dict(carrinho.itens)
        while not self.fechado:
            self.mexeu = False
            try:
                # O timeout é o "ocioso por 1 dia": cada mudança reinicia a espera.
                await workflow.wait_condition(lambda: self.mexeu or self.fechado, timeout=OCIOSO)
            except TimeoutError:
                return "abandonado"
            if workflow.info().is_continue_as_new_suggested():
                await workflow.wait_condition(workflow.all_handlers_finished)
                workflow.continue_as_new(Carrinho(cliente=carrinho.cliente, itens=self.itens))
        await workflow.wait_condition(workflow.all_handlers_finished)
        total = self.total_atual()
        await workflow.execute_activity(
            registrar_pedido,
            args=[carrinho.cliente, total],
            start_to_close_timeout=timedelta(seconds=10),
        )
        return f"fechado: R$ {total:.2f}"

    @workflow.update
    def adicionar(self, item: Item) -> float:
        antigo = self.itens.get(item.sku)
        qtd = item.quantidade + (antigo.quantidade if antigo else 0)
        self.itens[item.sku] = item.model_copy(update={"quantidade": qtd})
        self.mexeu = True
        return self.total_atual()

    @adicionar.validator
    def validar_adicionar(self, item: Item) -> None:
        if item.quantidade <= 0 or item.preco < 0:
            raise ValueError("quantidade e preço precisam ser positivos")
        if self.fechado:
            raise ValueError("carrinho já fechado")

    @workflow.update
    def remover(self, sku: str) -> float:
        del self.itens[sku]
        self.mexeu = True
        return self.total_atual()

    @remover.validator
    def validar_remover(self, sku: str) -> None:
        if self.fechado:
            raise ValueError("carrinho já fechado")
        if sku not in self.itens:
            raise ValueError(f"{sku} não está no carrinho")

    @workflow.update
    def fechar(self) -> float:
        self.fechado = True
        return self.total_atual()

    @workflow.query
    def total(self) -> float:
        return self.total_atual()
