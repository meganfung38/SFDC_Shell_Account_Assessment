import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Tuple, List, Dict

class AccountMatchingModel:
    """
    Decision tree model for analyzing account matching patterns.
    Identifies which field comparisons are most predictive of correct vs incorrect matches.
    """
    
    def __init__(self, max_depth=5, min_samples_split=2, random_state=42):
        self.model = DecisionTreeClassifier(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            random_state=random_state,
            criterion='gini'
        )
        self.feature_names = []
        self.feature_importance = None
        self.is_trained = False
        
    def train_model(self, features_df: pd.DataFrame) -> Dict:
        """
        Train the decision tree model on the feature data.
        
        Args:
            features_df: DataFrame with features and 'correctly_matched' labels
            
        Returns:
            Dictionary with training results and metrics
        """
        print("Training decision tree model...")
        
        # Prepare data
        label_col = 'correctly_matched'
        if label_col not in features_df.columns:
            raise ValueError(f"Missing label column '{label_col}' in features DataFrame")
        
        # Separate features and labels
        feature_cols = [col for col in features_df.columns 
                       if col not in ['correctly_matched', 'account_id']]
        
        X = features_df[feature_cols]
        y = features_df[label_col]
        
        # Handle any remaining NaN values
        X = X.fillna(0)
        
        self.feature_names = feature_cols
        print(f"Training on {len(feature_cols)} features with {len(y)} samples")
        print(f"Class distribution: {y.value_counts().to_dict()}")
        
        # Train the model
        self.model.fit(X, y)
        self.is_trained = True
        
        # Get feature importance
        self.feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Calculate training metrics
        y_pred = self.model.predict(X)
        training_accuracy = accuracy_score(y, y_pred)
        
        # Cross-validation (if we have enough samples)
        cv_scores = None
        if len(y) >= 5:  # Need at least 5 samples for CV
            cv_scores = cross_val_score(self.model, X, y, cv=min(5, len(y)), scoring='accuracy')
        
        results = {
            'training_accuracy': training_accuracy,
            'cross_val_scores': cv_scores,
            'cross_val_mean': cv_scores.mean() if cv_scores is not None else None,
            'cross_val_std': cv_scores.std() if cv_scores is not None else None,
            'feature_count': len(feature_cols),
            'sample_count': len(y),
            'class_distribution': y.value_counts().to_dict()
        }
        
        print(f"Training completed!")
        print(f"Training accuracy: {training_accuracy:.3f}")
        if cv_scores is not None:
            print(f"Cross-validation accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        return results
    
    def get_feature_importance(self, top_n: int = 20) -> pd.DataFrame:
        """Get the most important features for the decision tree."""
        if not self.is_trained:
            raise ValueError("Model must be trained first. Call train_model().")
        
        return self.feature_importance.head(top_n)
    
    def get_decision_rules(self, max_depth: int = 3) -> str:
        """Get human-readable decision tree rules."""
        if not self.is_trained:
            raise ValueError("Model must be trained first. Call train_model().")
        
        # Create a simpler tree for rule extraction
        simple_model = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
        
        # Use only top features for simpler rules
        top_features = self.feature_importance.head(10)['feature'].tolist()
        
        # We'll need the training data again - this is a limitation of this approach
        # For now, return the tree structure as text
        tree_rules = export_text(self.model, feature_names=self.feature_names, max_depth=max_depth)
        return tree_rules
    
    def predict_accounts(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Make predictions on new account data."""
        if not self.is_trained:
            raise ValueError("Model must be trained first. Call train_model().")
        
        feature_cols = [col for col in features_df.columns 
                       if col not in ['correctly_matched', 'account_id']]
        
        X = features_df[feature_cols].fillna(0)
        
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        
        results = features_df[['account_id']].copy()
        results['predicted_correct'] = predictions
        results['confidence_incorrect'] = probabilities[:, 0]  # Probability of class 0 (incorrect)
        results['confidence_correct'] = probabilities[:, 1]    # Probability of class 1 (correct)
        
        return results
    
    def analyze_feature_patterns(self) -> Dict:
        """Analyze patterns in the most important features."""
        if not self.is_trained:
            raise ValueError("Model must be trained first. Call train_model().")
        
        top_features = self.get_feature_importance(10)
        
        analysis = {
            'most_important_feature': top_features.iloc[0]['feature'],
            'most_important_importance': top_features.iloc[0]['importance'],
            'top_10_features': top_features['feature'].tolist(),
            'top_10_importances': top_features['importance'].tolist()
        }
        
        # Categorize features
        categories = {
            'name_features': [],
            'website_features': [], 
            'address_features': [],
            'zi_features': [],
            'exact_match_features': [],
            'other_features': []
        }
        
        for feature in analysis['top_10_features']:
            feature_lower = feature.lower()
            if 'name' in feature_lower:
                categories['name_features'].append(feature)
            elif 'website' in feature_lower or 'domain' in feature_lower:
                categories['website_features'].append(feature)
            elif any(addr in feature_lower for addr in ['city', 'state', 'country', 'address']):
                categories['address_features'].append(feature)
            elif 'zi_' in feature_lower:
                categories['zi_features'].append(feature)
            elif 'exact_match' in feature_lower:
                categories['exact_match_features'].append(feature)
            else:
                categories['other_features'].append(feature)
        
        analysis['feature_categories'] = categories
        
        return analysis
    
    def plot_feature_importance(self, top_n: int = 15, save_path: str = None):
        """Plot feature importance."""
        if not self.is_trained:
            raise ValueError("Model must be trained first. Call train_model().")
        
        top_features = self.get_feature_importance(top_n)
        
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(top_features)), top_features['importance'])
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Feature Importance')
        plt.title(f'Top {top_n} Most Important Features for Account Matching')
        plt.gca().invert_yaxis()
        
        # Color code by feature type
        colors = []
        for feature in top_features['feature']:
            if 'name' in feature.lower():
                colors.append('lightblue')
            elif 'website' in feature.lower() or 'domain' in feature.lower():
                colors.append('lightgreen')
            elif 'zi_' in feature.lower():
                colors.append('orange')
            elif 'exact_match' in feature.lower():
                colors.append('red')
            else:
                colors.append('gray')
        
        plt.barh(range(len(top_features)), top_features['importance'], color=colors)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def plot_decision_tree(self, max_depth: int = 3, save_path: str = None):
        """Plot the decision tree structure."""
        if not self.is_trained:
            raise ValueError("Model must be trained first. Call train_model().")
        
        # Create a simpler tree for visualization
        simple_model = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
        
        # Get top features for simpler visualization
        top_features = self.feature_importance.head(10)['feature'].tolist()
        
        plt.figure(figsize=(15, 10))
        
        # Note: This requires the training data which we don't have access to here
        # This is a limitation of the current design
        print("Decision tree visualization requires access to training data.")
        print("Use get_decision_rules() for text-based tree structure.")
    
    def print_comprehensive_analysis(self):
        """Print a comprehensive analysis of the model results."""
        if not self.is_trained:
            raise ValueError("Model must be trained first. Call train_model().")
        
        print("\n" + "="*80)
        print("DECISION TREE ANALYSIS RESULTS")
        print("="*80)
        
        # Feature importance analysis
        print("\n1. MOST IMPORTANT FEATURES:")
        print("-" * 40)
        top_features = self.get_feature_importance(10)
        for i, (_, row) in enumerate(top_features.iterrows()):
            print(f"{i+1:2d}. {row['feature']:<40} {row['importance']:.3f}")
        
        # Pattern analysis
        patterns = self.analyze_feature_patterns()
        print(f"\n2. KEY INSIGHTS:")
        print("-" * 40)
        print(f"• Most predictive feature: {patterns['most_important_feature']}")
        print(f"• Most predictive importance: {patterns['most_important_importance']:.3f}")
        
        # Feature categories
        print(f"\n3. FEATURE CATEGORY BREAKDOWN:")
        print("-" * 40)
        categories = patterns['feature_categories']
        for category, features in categories.items():
            if features:
                category_name = category.replace('_', ' ').title()
                print(f"• {category_name}: {len(features)} features")
                for feature in features[:3]:  # Show top 3
                    print(f"  - {feature}")
                if len(features) > 3:
                    print(f"  ... and {len(features) - 3} more")
        
        # Recommendations
        print(f"\n4. RECOMMENDATIONS:")
        print("-" * 40)
        
        most_important = patterns['most_important_feature'].lower()
        if 'name' in most_important:
            print("• Focus on improving name matching algorithms")
            print("• Company name similarity is the strongest predictor")
        elif 'website' in most_important or 'domain' in most_important:
            print("• Domain matching is highly predictive")
            print("• Focus on website/domain comparison logic")
        elif 'zi_' in most_important:
            print("• ZoomInfo fields are highly predictive")
            print("• Ensure ZI data quality and matching logic")
        
        # Show decision rules (simplified)
        print(f"\n5. DECISION TREE STRUCTURE (Top 3 levels):")
        print("-" * 40)
        try:
            rules = self.get_decision_rules(max_depth=3)
            # Truncate very long rules
            rules_lines = rules.split('\n')
            for line in rules_lines[:20]:  # Show first 20 lines
                print(line)
            if len(rules_lines) > 20:
                print("... (truncated for readability)")
        except Exception as e:
            print(f"Could not generate decision rules: {e}")
        
        print("\n" + "="*80)

def run_complete_analysis(excel_file_path: str):
    """Run the complete analysis pipeline."""
    from data_processor import AccountDataProcessor
    from feature_engineer import AccountFeatureEngineer
    
    print("Starting complete account matching analysis...")
    
    # 1. Load and process data
    processor = AccountDataProcessor(excel_file_path)
    processor.load_data()
    processor.print_data_summary()
    
    # 2. Create features
    engineer = AccountFeatureEngineer()
    features_df = engineer.create_all_features(
        processor.get_labeled_customers(),
        processor.get_shell_account()
    )
    engineer.print_feature_summary(features_df)
    
    # 3. Train model
    model = AccountMatchingModel()
    training_results = model.train_model(features_df)
    
    # 4. Analyze results
    model.print_comprehensive_analysis()
    
    # 5. Create visualizations
    print("\nCreating feature importance plot...")
    model.plot_feature_importance(save_path='feature_importance.png')
    
    return model, features_df, training_results

if __name__ == "__main__":
    # Run the complete analysis
    model, features_df, results = run_complete_analysis('Sample_ RC Account Hierarchy.xlsx')
    
    print(f"\nAnalysis complete!")
    print(f"Model trained on {results['sample_count']} samples")
    print(f"Training accuracy: {results['training_accuracy']:.3f}")
    
    # Show sample predictions
    predictions = model.predict_accounts(features_df)
    print(f"\nSample predictions:")
    print(predictions.head()) 