/* Handling stripe payment stuff */


var elements = stripe.elements();
var cardElement = elements.create('card');
cardElement.mount('#card-element');  
var form = document.getElementById('payment-form');

var resultContainer = document.getElementById('payment-result');
cardElement.on('change', function(event) {
  if (event.error) {
    resultContainer.textContent = event.error.message;
  } else {
    resultContainer.textContent = '';
  }
});

form.addEventListener('submit', function(event) {
  event.preventDefault();
  resultContainer.textContent = "";
  stripe.createPaymentMethod({
    type: 'card',
    card: cardElement,
  }).then(handlePaymentMethodResult);
});

function handlePaymentMethodResult(result) {
  if (result.error) {
    // An error happened when collecting card details, show it in the payment form
    resultContainer.textContent = result.error.message;

  } else {
    // Otherwise send paymentMethod.id to your server (see Step 3)
    fetch('/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ payment_method_id: result.paymentMethod.id })
    }).then(function(result) {
      return result.json();
      
    }).then(handleServerResponse);
  }
}

function handleServerResponse(responseJson) {

  if (responseJson.error) {
    // An error happened when charging the card, show it in the payment form
    if(responseJson.error.indexOf("required an authentication action") == -1){
        resultContainer.textContent = responseJson.error;
    }
    else{
        resultContainer.textContent = "We were unable to process payment with this card; please try another.";
    }
  } else {
    // Show a success message
    resultContainer.textContent = 'Thank you for your payment.';
    document.getElementById("go_on_link").style.display="block";
    document.getElementById("cart_cnt_span").style.display="none";
    if(document.getElementById("cart_cnt_span_mob") != null){
        document.getElementById("cart_cnt_span_mob").style.display="none";
    }
    document.getElementById('card-button').style.display="none";
  }
}