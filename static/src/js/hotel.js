function dateValidation() {
        let date_one = $('#filter_search').val();
        let date_two = $('#filter_search_end').val();
        let check_in_date = new Date(date_one)
        let check_out_date = new Date(date_two)
        if (check_in_date && check_out_date){
            if (check_out_date < check_in_date){
                $('#alert_message').append('It is not possible for the check-out date to exceed the check-in date.')
                $('#alert_message').addClass('alert-warning')
            } else if (check_out_date >= check_in_date){
                $('#alert_message').empty()
                $('#alert_message').removeClass('alert-warning')
            }
        }
}
