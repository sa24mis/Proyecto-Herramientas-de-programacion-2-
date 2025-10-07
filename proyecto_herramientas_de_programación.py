# ---- Dependencia (si no la tienes instalada) ----
!pip -q install yfinance

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

class AnalizadorFinanciero:
    """Descarga y analiza precios de acciones y la tasa 10Y usando Yahoo Finance (sin API key)."""

    def __init__(self, symbols):
        self.symbols = symbols
        self.stocks_df = pd.DataFrame()
        self.rate_df = pd.DataFrame()

    def descargar_acciones(self, period="1y", interval="1d"):
        """Descarga precios de cierre de las acciones desde Yahoo Finance."""
        data = yf.download(self.symbols, period=period, interval=interval, auto_adjust=False, progress=False)
        # Si viene MultiIndex, tomar 'Close'
        if isinstance(data.columns, pd.MultiIndex):
            data = data["Close"]
        data = data.dropna(how="all").sort_index()
        if data.empty:
            raise ValueError("No se obtuvieron datos de acciones. Revisa símbolos o periodo.")
        self.stocks_df = data
        print("✅ Acciones descargadas correctamente:", ", ".join(self.symbols))

    def descargar_tasa_interes(self, period="1y", interval="1d"):
        """Descarga la tasa del Treasury 10Y (^TNX) desde Yahoo Finance y la deja en %."""
        tnx = yf.download("^TNX", period=period, interval=interval, auto_adjust=False, progress=False)
        if tnx.empty:
            print("⚠️ No se obtuvieron datos de la tasa 10Y.")
            self.rate_df = pd.DataFrame()
            return

        close = tnx["Close"]                 # puede venir Serie o DataFrame
        if isinstance(close, pd.DataFrame):  # si es DF, convertir a Serie
            close = close.squeeze()

        rate_df = close.dropna().rename("US10Y").to_frame()
        rate_df["US10Y"] = rate_df["US10Y"] / 10.0  # ^TNX se reporta x10 → convertir a %
        rate_df = rate_df.sort_index()
        self.rate_df = rate_df
        print("✅ Tasa de interés US10Y descargada correctamente")

    def unir_datos(self):
        """Une la tasa de interés al DataFrame de acciones por índice de fecha."""
        if self.stocks_df.empty:
            raise ValueError("stocks_df está vacío. Llama primero a descargar_acciones().")
        df = self.stocks_df.copy()
        if not self.rate_df.empty:
            df = df.join(self.rate_df, how="left")
        self.stocks_df = df.ffill()

    def resumen_list_comprehensions(self):
        """Devuelve máximos, fechas de máximos, promedios y un resumen por símbolo."""
        maximos = [self.stocks_df[sym].max() for sym in self.symbols]
        fechas_maximos = [self.stocks_df[sym].idxmax() for sym in self.symbols]
        promedios = [self.stocks_df[sym].mean() for sym in self.symbols]
        resumen_maximos = [(sym, self.stocks_df[sym].max(), self.stocks_df[sym].idxmax()) for sym in self.symbols]
        return maximos, fechas_maximos, promedios, resumen_maximos

    def graficar(self, titulo="Acciones Tecnológicas y Tasa de Interés 10Y (Yahoo Finance)"):
        """Grafica acciones + tasa 10Y, con etiquetas visibles sobre cada línea."""
        if self.stocks_df.empty:
            raise ValueError("No hay datos para graficar. Descarga y une primero.")

        plt.figure(figsize=(12, 6))
        ax1 = plt.gca()

        # Nombres bonitos
        nombres = {
            "AAPL": "Apple",
            "AMZN": "Amazon",
            "MSFT": "Microsoft",
            "NVDA": "NVIDIA",
            "TSLA": "Tesla"
        }

        # Graficar acciones y poner etiqueta al final de cada línea
        for sym in self.symbols:
            if sym not in self.stocks_df.columns:
                continue
            ax1.plot(self.stocks_df.index, self.stocks_df[sym], label=sym)
            y = self.stocks_df[sym].iloc[-1]
            ax1.text(self.stocks_df.index[-1], y, f" {nombres.get(sym, sym)}",
                     va="center", fontsize=9, color=ax1.lines[-1].get_color())

        # Eje secundario para la tasa
        if "US10Y" in self.stocks_df.columns:
            ax2 = ax1.twinx()
            ax2.plot(self.stocks_df.index, self.stocks_df["US10Y"],
                     linestyle="--", color="black", label="Tasa US10Y (eje der)")
            ax2.set_ylabel("Tasa de Interés 10Y (%)", color="black")
            y_tasa = self.stocks_df["US10Y"].iloc[-1]
            ax2.text(self.stocks_df.index[-1], y_tasa, " Tasa 10Y",
                     va="center", fontsize=9, color="black")

            # Leyenda combinada
            l1, lab1 = ax1.get_legend_handles_labels()
            l2, lab2 = ax2.get_legend_handles_labels()
            ax1.legend(l1 + l2, lab1 + lab2, loc="upper left")
        else:
            ax1.legend(loc="upper left")

        ax1.set_title(titulo)
        ax1.set_xlabel("Fecha")
        ax1.set_ylabel("Precio Cierre (USD)")
        plt.tight_layout()
        plt.show()


# ------------ USO ------------
symbols = ["AAPL", "AMZN", "MSFT", "NVDA", "TSLA"]

analizador = AnalizadorFinanciero(symbols)
analizador.descargar_acciones(period="1y", interval="1d")
analizador.descargar_tasa_interes(period="1y", interval="1d")
analizador.unir_datos()
maximos, fechas_maximos, promedios, resumen_maximos = analizador.resumen_list_comprehensions()
analizador.graficar()
