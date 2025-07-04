<script lang="ts">
  import AccountInfo from '$lib/components/AccountInfo.svelte';
  import PositionsTable from '$lib/components/PositionsTable.svelte';
  import TradeForm from '$lib/components/TradeForm.svelte';

</script>

<svelte:head>
  <title>PyTrader Web UI</title>
</svelte:head>

<div class="app-container">
  <header>
    <h1>PyTrader Dashboard</h1>
  </header>

  <main>
    <section class="account-section">
      <AccountInfo />
    </section>

    <section class="trading-section">
      <TradeForm />
    </section>

    <section class="positions-section">
      <PositionsTable />
    </section>
  </main>

  <footer>
    <p>&copy; {new Date().getFullYear()} PyTrader. Alpaca API integration.</p>
  </footer>
</div>

<style>
  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
      Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    margin: 0;
    background-color: #f4f7f6;
    color: #333;
  }

  .app-container {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  header {
    background-color: #2c3e50;
    color: white;
    padding: 1rem 2rem;
    text-align: center;
  }

  header h1 {
    margin: 0;
    font-size: 1.8rem;
  }

  main {
    flex: 1;
    padding: 1rem;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
    box-sizing: border-box;
  }

  section {
    background-color: #ffffff;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  /* Assign grid areas if using CSS Grid for layout, or use flexbox */
  /* Example for main layout sections using flex for simplicity here */
  /*
  main {
    display: flex;
    flex-wrap: wrap; /* Allow wrapping on smaller screens */
    gap: 1.5rem;
  }

  .account-section, .trading-section {
    flex: 1; /* Each takes up half the space */
    min-width: 300px; /* Minimum width before wrapping */
  }

  .positions-section {
    flex-basis: 100%; /* Takes full width */
  }
  */


  footer {
    background-color: #34495e;
    color: white;
    text-align: center;
    padding: 1rem;
    font-size: 0.9rem;
  }

  /* Add more specific styles for h2 in components if needed, or style here */
  section h2 {
    margin-top: 0;
    color: #2c3e50;
    border-bottom: 2px solid #eaecee;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }
</style>
