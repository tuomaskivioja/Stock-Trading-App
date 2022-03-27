window.addEventListener('DOMContentLoaded', (event) => {
    chartFunction()
});

let config = {}

function chartFunction() {
  let symbols = document.querySelectorAll(".symbol");
  let holdingValues = document.querySelectorAll(".holdingValue");

  // list for colours, symbols and holding values. Initialize with one colour, cash & cash value (with comma removed to make the string into a float)
  let colours = [randomColour()];
  let symbolList = ['CASH']
  let holdingValuesList = [parseFloat(document.getElementById('cashValue').innerHTML.substring(1).replaceAll(',', ''))]

  //for each stock (+ cash), add the value and symbol to the arrays & generate a random colour
  symbols.forEach((symbol,i=0) => {
      symbolList.push(symbol.innerHTML)
      holdingValuesList.push(parseFloat(holdingValues[i].innerHTML.substring(1).replaceAll(',','')))
      colours.push(randomColour())
      i++
  })


  const data = {
      labels: symbolList,
      datasets: [{
        label: 'Holdings',
        data: holdingValuesList,
        backgroundColor: colours,
        hoverOffset: 4
      }],
      responsive: true
    };

  config = {
    type: 'pie',
    data: data,
  };
  //console.log(config)
}

//generate random rgb colour
function randomColour() {
    const r = () => Math.random() * 256 >> 0;
    return `rgb(${r()}, ${r()}, ${r()})`;
}