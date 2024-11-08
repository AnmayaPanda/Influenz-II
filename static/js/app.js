// Define a Vue component
Vue.component('campaign-list', {
    data: function() {
        return {
            campaigns: [],
        }
    },
    created: function() {
        // Fetch data from the server when the component is created
        fetch('/api/campaigns')
            .then(response => response.json())
            .then(data => {
                this.campaigns = data.campaigns;
            });
    },
    template: `
        <div>
            <h2>Campaigns</h2>
            <ul>
                <li v-for="campaign in campaigns" :key="campaign.id">
                    {{ campaign.name }} - {{ campaign.description }}
                </li>
            </ul>
        </div>
    `
});

// Initialize the Vue instance
new Vue({
    el: '#app'
});
