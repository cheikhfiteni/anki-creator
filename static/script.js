const topicForm = document.getElementById('topicForm');
const cardsContainer = document.getElementById('cardsContainer');
const addToAnkiButton = document.getElementById('addToAnki');
const viewDeckCardsButton = document.getElementById('viewDeckCards');
const deckSelect = document.getElementById('deckSelect');

async function loadDecks() {
    const response = await fetch('/decks');
    const data = await response.json();
    console.log("data", data)
    deckSelect.innerHTML = '<option value="">Select a deck</option>';
    data.decks.forEach(deck => {
        const option = document.createElement('option');
        option.value = deck;
        option.textContent = deck;
        deckSelect.appendChild(option);
    });
}

loadDecks();

topicForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const topic = document.getElementById('topic').value;
    const deckName = deckSelect.value;
    if (!deckName) {
        alert('Please select a deck');
        return;
    }
    const response = await fetch('/generate_cards', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({ topic, deck_name: deckName }),
    });
    const data = await response.json();
    displayCards(data.cards);
});

function displayCards(cards) {
    cardsContainer.innerHTML = '';
    cards.forEach((card, index) => {
        const cardElement = document.createElement('div');
        cardElement.className = 'bg-gray-200 p-4 rounded';
        cardElement.innerHTML = `
            <h3 class="font-bold mb-2">Card ${index + 1}</h3>
            <p><strong>Front:</strong> ${card.front}</p>
            <p><strong>Back:</strong> ${card.back}</p>
            <button class="remove-card bg-red-500 text-white p-1 rounded mt-2">Remove</button>
        `;
        cardsContainer.appendChild(cardElement);
    });
    addToAnkiButton.classList.remove('hidden');
}

cardsContainer.addEventListener('click', (e) => {
    if (e.target.classList.contains('remove-card')) {
        e.target.closest('div').remove();
        if (cardsContainer.children.length === 0) {
            addToAnkiButton.classList.add('hidden');
        }
    }
});

addToAnkiButton.addEventListener('click', async () => {
    const deckName = deckSelect.value;
    if (!deckName) {
        alert('Please select a deck');
        return;
    }
    const cards = Array.from(cardsContainer.children).map(cardElement => {
        const [front, back] = cardElement.querySelectorAll('p');
        return {
            front: front.textContent.replace('Front: ', ''),
            back: back.textContent.replace('Back: ', '')
        };
    });

    const response = await fetch('/add_cards', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            deck_name: deckName,
            cards: cards
        }),
    });
    const result = await response.json();
    alert('Cards added to Anki successfully!');
    cardsContainer.innerHTML = '';
    addToAnkiButton.classList.add('hidden');
});

viewDeckCardsButton.addEventListener('click', async () => {
    const deckName = deckSelect.value;
    if (!deckName) {
        alert('Please select a deck');
        return;
    }
    const response = await fetch(`/cards/${encodeURIComponent(deckName)}`);
    const data = await response.json();
    displayCards(data.cards);
});
