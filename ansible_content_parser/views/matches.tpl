% include("head.tpl")

<div class="container">
  <div class="row">
    <table id="example" class="table table-striped table-bordered" cellspacing="0" width="100%">
      <thead>
      <tr>
        <th>Rule</th>
        <th>Message</th>
        <th>Location</th>
      </tr>
      </thead>
      <tbody role="rowgroup">
      % for match in matches:
      <tr role="row">
        <td>
          <a href="{{ match['url'] }}">
            {{ match['check_name'] }}
          </a>
        </td>
        <td>{{match['description']}}</td>
        <td>{{ match['location']['path'] }}
          % if 'positions' in match['location']:
            % if 'begin' in match['location']['positions']:
              :{{ match['location']['positions']['begin']['line'] }}
              % if 'column' in match['location']['positions']['begin']:
                :{{ match['location']['positions']['begin']['column'] }}
              % end
            % end
          % elif 'lines' in match['location']:
            % if 'begin' in match['location']['lines']:
              :{{ match['location']['lines']['begin'] }}
            % end
          % end
        </td>
      </tr>
      % end
      </tbody>
    </table>
  </div>
</div>

<script>
  $(document).ready(function() {
  $("#example").DataTable({
   "pageLength": 25
  });
});
</script>