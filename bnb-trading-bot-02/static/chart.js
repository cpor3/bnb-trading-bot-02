chart_div_width = document.getElementById("chart").offsetWidth;
chart_div_height = document.getElementById("results").offsetHeight;
chart_trades_div_width = document.getElementById("chart_trades").offsetWidth;
colorGrilla = 'rgb(32, 35, 41)';
colorEjes = 'rgb(94, 102, 115)';
colorFondo = 'rgb(25, 27, 32)'

//Ajustar los tamaños de los graficos  
document.getElementById("body_simular").onresize = function() {
    //chart velas
    chart_div_width = document.getElementById("chart").offsetWidth;
    chart_div_height = document.getElementById("results").offsetHeight;

    chart.applyOptions({
        width: chart_div_width,
        height: chart_div_height,
    });
    
    //chart rendimiento
    chart_trades_div_width = document.getElementById("chart_trades").offsetWidth;

    chart_trades.applyOptions({
        width: chart_trades_div_width
    });

    chart_trades.timeScale().fitContent(); 
};

//Grafico de velas
var chart = LightweightCharts.createChart(document.getElementById("chart"), {
    width: chart_div_width,
    height: chart_div_height,
    rightPriceScale: {
        visible: true,
        borderColor: colorEjes,
    },
    layout: {
        backgroundColor: colorFondo,
        textColor: colorEjes,
        fontSize: 10,
    },
    grid: {
        horzLines: {
          color: colorGrilla,
        },
        vertLines: {
          color: colorGrilla,
        },
    },
    crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
    },
    timeScale: {
        borderColor: colorEjes,
        timeVisible: true,
        secondsVisible: false,
        // tickMarkFormatter: (time, tickMarkType, locale) => {
        //     console.log(time, tickMarkType, locale);
        //     console.log(time.toString());
        //     return time.toString();
        // },
    },
    handleScroll: {
        vertTouchDrag: false,
    },    
    localization: {
        locale: 'es-ES',
        dateFormat: 'yyyy/MM/dd',
        priceFormatter: price => price.toFixed(price_precision),
    }, 
    watermark: {
        color: colorGrilla,
        visible: true,
        text: 'BNB-TRADING-BOT-01',
        fontSize: 48,
        horzAlign: 'center',
        vertAlign: 'center',
    },
});

const candlestickSeries = chart.addCandlestickSeries({ 
    priceScaleId: 'right', 
    upColor: 'rgba(2, 192, 118, 1)', 
    downColor: 'rgba(207, 48, 74, 1)',
    wickUpColor: 'rgba(2, 192, 118, 1)', 
    wickDownColor: 'rgba(207, 48, 74, 1)',
    borderUpColor: 'rgba(2, 192, 118, 1)', 
    borderDownColor: 'rgba(207, 48, 74, 1)',
    priceFormat: {
        type: 'volume',
        precision: price_precision,
        minMove: 0.0001,
    },
    priceLineVisible: false,        
});

candlestickSeries.setData(klines_js);

const maLine = chart.addLineSeries({
    color: 'rgba(4, 232, 4, 1)',
    lineWidth: 1,
    priceLineVisible: false,        
});

maLine.setData(MA_js);

//console.log('trades_js: ', trades_js);
//console.log('klines_js: ', klines_js);

//Mostrar momentos de compra y venta
var markers = [];

for (var i=0; i<trades_js.length; i++) {
    if (trades_js[i].side == 'BUY') {
        markers.push({
              time: trades_js[i].time,
              position: 'inBar',
              color: 'rgba(0, 100, 200, 1)',
              shape: 'circle',
              text: ''    
        })
        markers.push({
              time: trades_js[i].time,
              position: 'belowBar',
              color: 'rgba(0, 100, 200, 1)',
              shape: 'arrowUp',
              text: 'Buy @ ' + trades_js[i].price.toFixed(price_precision)    
        })
    }
    else {
        markers.push({
              time: trades_js[i].time,
              position: 'inBar',
              color: 'rgba(200, 200, 0, 1)',
              shape: 'circle',
              text: ''   
        })
        markers.push({
              time: trades_js[i].time,
              position: 'aboveBar',
              color: 'rgba(200, 200, 0, 1)',
              shape: 'arrowDown',
              text: 'Sell @ ' + trades_js[i].price.toFixed(price_precision)    
        })
    }    
}

candlestickSeries.setMarkers(markers);

//Grafico de rendimiento
var chart_trades = LightweightCharts.createChart(document.getElementById("chart_trades"), {
    width: chart_trades_div_width,
    height: 300,
    rightPriceScale: {
        visible: true,
        borderColor: colorEjes,
    },
    layout: {
        backgroundColor: colorFondo,
        textColor: colorEjes,
        fontSize: 10,
    },
    grid: {
        horzLines: {
          color: colorGrilla,
        },
        vertLines: {
          color: colorGrilla,
        },
    },
    crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
    },
    timeScale: {
        visible: false,
        borderColor: colorEjes,
        timeVisible: true,
        secondsVisible: false,
    },
    handleScroll: {
        vertTouchDrag: false,
    },    
    localization: {
        dateFormat: 'yyyy/MM/dd',
    }, 
});

//Ajustar fomarto de la data para graficar
var trades_js_formatted = trades_js.map(({time, strategy_result}) => ({time: time, value: strategy_result}))
//console.log(trades_js_formatted);

//Ver si el rendimiento fue positivo (graficar en verde) o negativo (graficar en rojo)
end_result = trades_js[trades_js.length - 1]['strategy_result']
//console.log("end_result: " + end_result)
if (end_result >= 0) {
    var _topColor = 'rgba(76, 175, 80, 0.56)';
    var _bottomColor = 'rgba(76, 175, 80, 0.04)';
    var _lineColor = 'rgba(76, 175, 80, 1)';
}
else
{
    var _topColor = 'rgba(175, 36, 0, 0.56)';
    var _bottomColor = 'rgba(175, 36, 0, 0.04)';
    var _lineColor = 'rgba(175, 36, 0, 1)';
}

areaSeries = chart_trades.addAreaSeries({
    topColor: _topColor,
    bottomColor: _bottomColor,
    lineColor: _lineColor,
    lineWidth: 2,
    priceFormat: {
        type: 'volume',
        precision: price_precision,
        minMove: 0.0001,
    },
    priceLineVisible: false,        
});

areaSeries.setData(trades_js_formatted);

//Ajustar escala x al contenido
chart_trades.timeScale().fitContent();