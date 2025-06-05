Fairness Pipeline Documentation
===============================

1. Data Cleaning
----------------

.. code-block:: python

  PATH = 'C:/Users/andre/Desktop/ProjectWork_AEQUITAS_AKKODIS/'
  df = (
      pd.read_excel(PATH + 'data/Dataset_2.0_Akkodis.xlsx')
        .rename(columns=lambda c: c.lstrip().title())
  )

  df = df.drop_duplicates(subset='Id', keep='last')

  df = df.drop(columns=config['drop_columns'])

  for col, remove_list in config['drop_rows'].items():
      df = df[~df[col].isin(remove_list)]

  for col, mapping in config['remap_rows'].items():
      df[col] = df[col].replace(mapping)

.. code-block:: python

  unuseful_columns = []
  for col in df.columns:
    null_count = df[col].isna().sum() / df.shape[0]
    if null_count > (float(config['drop_nan_columns_threshold'])/100):
      unuseful_columns.append(col)
  df = df.drop(columns=unuseful_columns)

  for col, filler in config['fill_nan_columns'].items():
      if filler == '%MEAN%':
          media = round(df[col].mean())
          df[col].fillna(media, inplace=True)
      else:
          df[col].fillna(filler, inplace=True)

.. code-block:: python

  def gen_lists(df, specs):
      out = {}
      for name, p in specs.items():
          base = out.get(p['src'], df[p['src']].dropna().astype(str).unique())
          items = [
              x for x in base
              if not any(exc in x for exc in p.get('exc', []))
                and (any(inc in x for inc in p.get('inc', [])) if 'inc' in p else True)
          ]
          for key in ('split', 'post'):
              if key in p:
                  sep, idx = p[key]
                  items = [x.split(sep)[idx] if sep in x else x for x in items]
          out[name] = sorted(set(items))
      return out

  def apply_field(val, p, lists, feature_cfg):
      if 'list' in p:
          return next((x for x in lists[p['list']] if x in str(val)), p['def'])
      if 'in' in p:
          return p['y'] if val in feature_cfg[p['in']] else p['n']
      if 'eq' in p:
          return p['y'] if str(val) == p['eq'] else p['n']

  for feature, feat_cfg in config['feature_remapping'].items():
      lists = gen_lists(df, feat_cfg['lists'])
      for col_name, col_cfg in feat_cfg['fields'].items():
          df[col_name] = df[col_cfg['src']].apply(lambda v, cfg=col_cfg: apply_field(v, cfg, lists, feat_cfg))
      df = df.drop(columns=feature, errors='ignore')

.. code-block:: python

  mask = np.zeros(len(df), dtype=bool)
  for col, valid_values in config['status_positive_conditions'].items():
      mask |= df[col].isin(valid_values)
  df['Status'] = np.where(mask, 'Positive', 'Negative')

2. Data Loading & Understanding
-------------------------------
2.1 Feature Selection
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  stats = pd.DataFrame(index=df.columns)
  stats['missing_values'] = df.isnull().sum()
  stats['min'] = df.min(numeric_only=True)
  stats['max'] = df.max(numeric_only=True)
  stats['mean'] = df.mean(numeric_only=True)
  stats['std'] = df.std(numeric_only=True)
  stats['1st_percentile'] = df.quantile(0.25, numeric_only=True)
  stats['2nd_percentile'] = df.quantile(0.50, numeric_only=True)
  stats['3rd_percentile'] = df.quantile(0.75, numeric_only=True)
  stats['type'] = df.dtypes
  stats['distinct_values'] = df.nunique()

  for lookup in config['visualize_columns']:
      distrib = Counter(df[lookup])
      labels = config['categorical_columns_custom_orders'].get(lookup, distrib.keys())
      counts = [distrib[label] for label in labels]
      distrib_df = pd.DataFrame({lookup: labels, 'Count': counts})
      distrib_df.head(20).plot(x=lookup, y='Count', kind='bar', legend=False)
      plt.title(lookup)

Inoltre:
- Identificazione delle **feature sensibili** (es. genere, etnia, età)
- Definizione della **feature target** (es. assunto/sì-no)

.. code-block:: python

  for snstv_col in config['visualize_distributions_columns_by_feature']:
      order = config['categorical_columns_custom_orders'].get(snstv_col)

      pivot = df.pivot_table(
          index=snstv_col,
          columns='Status',
          aggfunc='size',
          fill_value=0
      )
      if order:
          pivot = pivot.reindex(order)
      pivot_pct = pivot.div(pivot.sum(axis=1), axis=0)
      pivot_pct.plot(kind='bar', stacked=True, figsize=(10, 6))
      plt.title(f"Distribution of Status by {snstv_col} (Normalized)")
      plt.xticks(rotation=45)
      plt.legend(title='Status', loc='upper left')

      df_plot = df.copy()
      if order:
          df_plot[snstv_col] = pd.Categorical(df_plot[snstv_col], categories=order, ordered=True)
      plt.figure(figsize=(10, 6))
      sns.histplot(
          data=df_plot,
          x=snstv_col,
          hue="Status",
          multiple="stack",
          palette="Set3",
          shrink=0.9,
      )
      plt.title(f"Distribution of Status by {snstv_col}", fontsize=14)
      plt.xticks(rotation=45)

.. code-block:: python

  for snstv_col in config['visualize_distributions_columns_by_status']:
    order = config['categorical_columns_custom_orders'].get(snstv_col)

    df_plot = df.copy()
    if order:
        df_plot[snstv_col] = pd.Categorical(df_plot[snstv_col], categories=order, ordered=True)
    plt.figure(figsize=(8, 5))
    sns.boxplot(
        data=df_plot,
        x="Status",
        y=snstv_col,
        palette="Set3",
        hue="Status",
    )
    plt.title(f"{snstv_col} distribution by Status", fontsize=14)
    plt.xticks(rotation=45)

2.2 Proxy Identification
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
  
  columns_type = {}
  for col in df.columns:
      if pd.api.types.is_string_dtype(df[col]):
          columns_type[col] = 'cat'
      elif pd.api.types.is_numeric_dtype(df[col]):
          columns_type[col] = 'num'
  pprint(columns_type)

.. code-block:: python

  num_cols = [col for col, t in columns_type.items() if t == 'num']
  df_num = df[num_cols].copy()

  plt.figure(figsize=(18, 12))
  sns.heatmap(df_num.corr().round(2), annot=True, cmap='coolwarm', center=0, linewidths=.5)

.. code-block:: python

  for col in [col for col, t in columns_type.items() if t == 'cat']:
      if col == 'Status':
          continue  # Skip Status as it is already handled separately

      order = config['categorical_columns_custom_orders'].get(col)

      contingency = pd.crosstab(df[col], df['Status'])
      
      if order:
          contingency = contingency.reindex(index=order)
      
      chi2, p, dof, expected = chi2_contingency(contingency, correction=False)
      test_name = 'Chi-squared'
      if contingency.shape == (2, 2) and (expected < 5).any():
          _, p = fisher_exact(contingency)
          test_name = "Fisher's exact"
      n = contingency.values.sum()
      k = min(contingency.shape)
      cramer_v = np.sqrt(chi2 / (n * (k - 1)))
      
      if p < 0.05:
          print(f"--- {col} ---")
          print("Actual frequencies:")
          print(contingency)
          print()
          print("Expected frequencies:")
          print(pd.DataFrame(expected, index=contingency.index, columns=contingency.columns))
          print()
          print(f"{test_name} test: χ² = {chi2:.2f}, p = {p:.3f}, dof = {dof}, Cramér’s V = {cramer_v:.3f}")
          print("Conclusion: Significant association (Dependent)")
          print()

2.3 Bias Detection
~~~~~~~~~~~~~~~~~~

.. code-block:: python
  
    def compute_bias_metrics(df, sensitive_column, target_column):
        y_true = (df[target_column] == 'Positive').astype(int)
        s_attr = df[sensitive_column]

        dpd = demographic_parity_difference(y_true, y_true, sensitive_features=s_attr)

        mf = MetricFrame(metrics=selection_rate, y_true=y_true, y_pred=y_true, sensitive_features=s_attr)
        sr_by_group = mf.by_group
        di = sr_by_group.min() / sr_by_group.max()

        print(f"\n=== Bias metrics for: {sensitive_column} ===")
        print(f"Statistical Parity Difference: {dpd:.4f}")
        print(f"Disparate Impact (min/max rate): {di:.4f}")
        print("\nSelection Rates by group:")
        print(sr_by_group)

    for sensitive_attr in config['sensitive_columns']:
        compute_bias_metrics(df, sensitive_attr, 'Status')

3. Training and Testing
-----------------------
encoding_mappings = {}
for col in [col for col, t in columns_type.items() if t == 'cat']:
    if col in config['categorical_columns_custom_orders']:
        df[col] = pd.Categorical(df[col], categories=config['categorical_columns_custom_orders'][col], ordered=True).codes
        encoding_mappings[col] = {cat: i for i, cat in enumerate(config['categorical_columns_custom_orders'][col])}
    else:
        encoder = LabelEncoder()
        df[col] = encoder.fit_transform(df[col].astype(str))
        encoding_mappings[col] = dict(zip(encoder.classes_, encoder.transform(encoder.classes_)))

- **Performance bar-plot**
  - Accuracy
  - Precision
  - Recall
  - F1-score
  - AUC

.. code-block:: python

  metrics = []
  for name in predictions_df.columns:
      y_pred = predictions_df[name]
      accuracy = round(accuracy_score(y_test, y_pred), 3)
      precision = round(precision_score(y_test, y_pred), 3)
      recall = round(recall_score(y_test, y_pred), 3)
      f1 = round(f1_score(y_test, y_pred), 3)
      roc_auc = round(roc_auc_score(y_test, y_pred), 3)

      metrics.append({
          'Model': name,
          'Accuracy': accuracy,
          'Precision': precision,
          'Recall': recall,
          'F1-score': f1,
          'ROC AUC': roc_auc
      })
  metrics = pd.DataFrame(metrics)


- **Fairness bar-plot**
  - Demographic Parity Ratio
  - Equalized Odds Ratio

.. code-block:: python
  def compute_fairness_metrics(y_true, y_pred, s_test, label=None):
      mf = MetricFrame(
          metrics={
              'selection_rate': selection_rate,
              'fpr': false_positive_rate,
              'fnr': false_negative_rate,
              'count': count
          },
          y_true=y_true,
          y_pred=y_pred,
          sensitive_features=s_test
      )

      dp_diff = demographic_parity_difference(y_true, y_pred, sensitive_features=s_test)
      eo_diff = equalized_odds_difference(y_true, y_pred, sensitive_features=s_test)

      dp = demographic_parity_ratio(y_true, y_pred, sensitive_features=s_test)
      eo = equalized_odds_ratio(y_true, y_pred, sensitive_features=s_test)

      if label:
          print(f"=== {label} ===")

      print("By group:")
      print(mf.by_group)
      print()
      print("Overall (selection_rate, fpr, fnr, count):")
      print(mf.overall)
      print()
      print(f"Demographic parity difference: {dp_diff:.4f}")
      print(f"Equalized odds difference:     {eo_diff:.4f}\n")
      print()
      print(f"Demographic parity ratio: {dp:.4f}")
      print(f"Equalized odds ratio:     {eo:.4f}\n")

      return mf
  for name in predictions_df.columns:
      compute_fairness_metrics(y_test, predictions_df[name], s_test, label=name)

3.1 Pre-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Performance bar-plot**
  - Accuracy
  - Precision
  - Recall
  - F1-score
  - AUC

.. code-block:: python

  metrics = []
  for name in predictions_df.columns:
      y_pred = predictions_df[name]
      accuracy = round(accuracy_score(y_test, y_pred), 3)
      precision = round(precision_score(y_test, y_pred), 3)
      recall = round(recall_score(y_test, y_pred), 3)
      f1 = round(f1_score(y_test, y_pred), 3)
      roc_auc = round(roc_auc_score(y_test, y_pred), 3)

      metrics.append({
          'Model': name,
          'Accuracy': accuracy,
          'Precision': precision,
          'Recall': recall,
          'F1-score': f1,
          'ROC AUC': roc_auc
      })
  metrics = pd.DataFrame(metrics)


- **Fairness bar-plot**
  - Demographic Parity Ratio
  - Equalized Odds Ratio

.. code-block:: python
  def compute_fairness_metrics(y_true, y_pred, s_test, label=None):
      mf = MetricFrame(
          metrics={
              'selection_rate': selection_rate,
              'fpr': false_positive_rate,
              'fnr': false_negative_rate,
              'count': count
          },
          y_true=y_true,
          y_pred=y_pred,
          sensitive_features=s_test
      )

      dp_diff = demographic_parity_difference(y_true, y_pred, sensitive_features=s_test)
      eo_diff = equalized_odds_difference(y_true, y_pred, sensitive_features=s_test)

      dp = demographic_parity_ratio(y_true, y_pred, sensitive_features=s_test)
      eo = equalized_odds_ratio(y_true, y_pred, sensitive_features=s_test)

      if label:
          print(f"=== {label} ===")

      print("By group:")
      print(mf.by_group)
      print()
      print("Overall (selection_rate, fpr, fnr, count):")
      print(mf.overall)
      print()
      print(f"Demographic parity difference: {dp_diff:.4f}")
      print(f"Equalized odds difference:     {eo_diff:.4f}\n")
      print()
      print(f"Demographic parity ratio: {dp:.4f}")
      print(f"Equalized odds ratio:     {eo:.4f}\n")

      return mf
  for name in predictions_df.columns:
      compute_fairness_metrics(y_test, predictions_df[name], s_test, label=name)

3.2 In-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Performance bar-plot**
  - Accuracy
  - Precision
  - Recall
  - F1-score
  - AUC

.. code-block:: python

  metrics = []
  for name in predictions_df.columns:
      y_pred = predictions_df[name]
      accuracy = round(accuracy_score(y_test, y_pred), 3)
      precision = round(precision_score(y_test, y_pred), 3)
      recall = round(recall_score(y_test, y_pred), 3)
      f1 = round(f1_score(y_test, y_pred), 3)
      roc_auc = round(roc_auc_score(y_test, y_pred), 3)

      metrics.append({
          'Model': name,
          'Accuracy': accuracy,
          'Precision': precision,
          'Recall': recall,
          'F1-score': f1,
          'ROC AUC': roc_auc
      })
  metrics = pd.DataFrame(metrics)


- **Fairness bar-plot**
  - Demographic Parity Ratio
  - Equalized Odds Ratio

.. code-block:: python
  def compute_fairness_metrics(y_true, y_pred, s_test, label=None):
      mf = MetricFrame(
          metrics={
              'selection_rate': selection_rate,
              'fpr': false_positive_rate,
              'fnr': false_negative_rate,
              'count': count
          },
          y_true=y_true,
          y_pred=y_pred,
          sensitive_features=s_test
      )

      dp_diff = demographic_parity_difference(y_true, y_pred, sensitive_features=s_test)
      eo_diff = equalized_odds_difference(y_true, y_pred, sensitive_features=s_test)

      dp = demographic_parity_ratio(y_true, y_pred, sensitive_features=s_test)
      eo = equalized_odds_ratio(y_true, y_pred, sensitive_features=s_test)

      if label:
          print(f"=== {label} ===")

      print("By group:")
      print(mf.by_group)
      print()
      print("Overall (selection_rate, fpr, fnr, count):")
      print(mf.overall)
      print()
      print(f"Demographic parity difference: {dp_diff:.4f}")
      print(f"Equalized odds difference:     {eo_diff:.4f}\n")
      print()
      print(f"Demographic parity ratio: {dp:.4f}")
      print(f"Equalized odds ratio:     {eo:.4f}\n")

      return mf
  for name in predictions_df.columns:
      compute_fairness_metrics(y_test, predictions_df[name], s_test, label=name)

3.3 Post-processing Mitigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Performance bar-plot**
  - Accuracy
  - Precision
  - Recall
  - F1-score
  - AUC

.. code-block:: python

  metrics = []
  for name in predictions_df.columns:
      y_pred = predictions_df[name]
      accuracy = round(accuracy_score(y_test, y_pred), 3)
      precision = round(precision_score(y_test, y_pred), 3)
      recall = round(recall_score(y_test, y_pred), 3)
      f1 = round(f1_score(y_test, y_pred), 3)
      roc_auc = round(roc_auc_score(y_test, y_pred), 3)

      metrics.append({
          'Model': name,
          'Accuracy': accuracy,
          'Precision': precision,
          'Recall': recall,
          'F1-score': f1,
          'ROC AUC': roc_auc
      })
  metrics = pd.DataFrame(metrics)


- **Fairness bar-plot**
  - Demographic Parity Ratio
  - Equalized Odds Ratio

.. code-block:: python
  def compute_fairness_metrics(y_true, y_pred, s_test, label=None):
      mf = MetricFrame(
          metrics={
              'selection_rate': selection_rate,
              'fpr': false_positive_rate,
              'fnr': false_negative_rate,
              'count': count
          },
          y_true=y_true,
          y_pred=y_pred,
          sensitive_features=s_test
      )

      dp_diff = demographic_parity_difference(y_true, y_pred, sensitive_features=s_test)
      eo_diff = equalized_odds_difference(y_true, y_pred, sensitive_features=s_test)

      dp = demographic_parity_ratio(y_true, y_pred, sensitive_features=s_test)
      eo = equalized_odds_ratio(y_true, y_pred, sensitive_features=s_test)

      if label:
          print(f"=== {label} ===")

      print("By group:")
      print(mf.by_group)
      print()
      print("Overall (selection_rate, fpr, fnr, count):")
      print(mf.overall)
      print()
      print(f"Demographic parity difference: {dp_diff:.4f}")
      print(f"Equalized odds difference:     {eo_diff:.4f}\n")
      print()
      print(f"Demographic parity ratio: {dp:.4f}")
      print(f"Equalized odds ratio:     {eo:.4f}\n")

      return mf
  for name in predictions_df.columns:
      compute_fairness_metrics(y_test, predictions_df[name], s_test, label=name)
