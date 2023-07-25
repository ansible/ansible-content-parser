% include("head.tpl")

<div class="container">
  <div class="row">
    <table id="example" class="table table-striped table-bordered" cellspacing="0" width="100%">
      <thead>
      <tr>
        <th>File names</th>
        <th>Kind</th>
        <th>Role</th>
      </tr>
      </thead>
      <tbody role="rowgroup">
      % for file in files:
      <tr role="row">
        <td>{{ file['filename'] }}</td>
        % if file['kind'] in ['playbook', 'tasks', 'jinja2', 'vars', 'handlers']:
          <td><span class="badge badge-{{ file['kind'] }}")>{{ file['kind'] }}</span></td>
        % else:
          <td><span class="badge badge-default")>{{ file['kind'] }}</span></td>
        % end
        <td>{{ file['role'] }}</td>
      </tr>
      % end
      </tbody>
    </table>
  </div>
</div>

<script>
  $(document).ready(function() {
  $("#example").DataTable({
    "pageLength": 25,
    "order": [[ 0, 'desc' ]]
  });
});
</script>
