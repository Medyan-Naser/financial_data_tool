import pandas as pd

def merge_index(df1, df2):
    custom_merged = []
    df1_index = df1.index.tolist()
    df2_index = df2.index.tolist()
    size_of_index_1 = len(df1_index)
    size_of_index_2 = len(df2_index)
    second_index = 0
    first_index = 0

    while first_index < size_of_index_1:  # Use a while loop for better control
        if first_index < size_of_index_1 and second_index < size_of_index_2:
            if df1_index[first_index] == df2_index[second_index]:
                custom_merged.append(df1_index[first_index])
                second_index += 1
                first_index += 1
            elif df1_index[first_index] not in df2_index:
                # Index in df1 but not in df2
                custom_merged.append(df1_index[first_index])
                first_index += 1
            else:
                # Handle the case where the index is in df2 but not in df1
                while second_index < size_of_index_2:
                    if df1_index[first_index] == df2_index[second_index]:
                        custom_merged.append(df1_index[first_index])
                        second_index += 1
                        first_index += 1
                        break  # Exit the inner loop once matched
                    else:
                        custom_merged.append(df2_index[second_index])
                        second_index += 1
        elif second_index >= size_of_index_2:
            # Add the remaining elements from df1
            custom_merged.extend(df1_index[first_index:])
            break
        else:
            break

    # Add remaining elements from df2, if any
    if second_index < size_of_index_2:
        custom_merged.extend(df2_index[second_index:])

    return custom_merged


def merge_dfs(df1, df2):
    # Initialize an empty DataFrame for the merged result
    merged_df = pd.DataFrame()
    custom_merged = merge_index(df1, df2)
    df1 = df1.reindex(index=custom_merged, fill_value=0)
    df2 = df2.reindex(index=custom_merged, fill_value=0)
    # Merge columns from df1
    for column in df1.columns:
        merged_df[column] = df1[column]
    # Merge columns from df2 that are not already in df1
    for column in df2.columns:
        if column not in df1.columns:
            merged_df[column] = df2[column]
    # Sort the columns to sort by date
    merged_df = merged_df.sort_index(axis=1, ascending=False)
    return merged_df