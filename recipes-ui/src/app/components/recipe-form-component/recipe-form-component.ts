import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormArray, FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

// Angular Material Imports
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { RecipeService } from '../../services/recipe.service';
import { Ingredient, Recipe, RecipePart } from '../../models/recipes.model';
     // Adjust import path

@Component({
  selector: 'app-recipe-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatDividerModule,
    MatSnackBarModule
  ],
  templateUrl: './recipe-form-component.html',
  styleUrl: './recipe-form-component.css'
})
export class RecipeFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private recipeService = inject(RecipeService);
  private snackBar = inject(MatSnackBar);

  recipeForm!: FormGroup;
  isEditMode = false;
  recipeId: string | null = null;
  isLoading = false;

  ngOnInit(): void {
    this.initForm();

    this.recipeId = this.route.snapshot.paramMap.get('id');
    if (this.recipeId) {
      this.isEditMode = true;
      this.loadRecipeData(this.recipeId);
    } else {
      // Initialize with at least one default Part
      this.addPart();
    }
  }
  // --- Form Initialization ---
  private initForm(): void {
    this.recipeForm = this.fb.group({
      title: ['', [Validators.required, Validators.minLength(3)]],
      description: ['', [Validators.required]],
      imageUrl: [''],
      prepTimeMinutes: [15, [Validators.required, Validators.min(1)]],
      cookTimeMinutes: [15, [Validators.required, Validators.min(0)]],
      servings: [4, [Validators.required, Validators.min(1)]],
      totalWeightGrams: [null],
      costPer100g: [null],
      caloriesPer100g: [null],
      parts: this.fb.array([])
    });
  }

  // --- FormArray Getters ---
  get parts(): FormArray {
    return this.recipeForm.get('parts') as FormArray;
  }

  getPartIngredients(partIndex: number): FormArray {
    return this.parts.at(partIndex).get('ingredients') as FormArray;
  }

  getPartInstructions(partIndex: number): FormArray {
    return this.parts.at(partIndex).get('instructions') as FormArray;
  }

  // --- Part Builders & Actions ---
createPartGroup(part?: RecipePart): FormGroup {
  // 1. Explicitly specify <FormGroup> or <AbstractControl> for the FormArray
  const ingredientsFormArray = this.fb.array<FormGroup>([]);
  
  if (part?.ingredients?.length) {
    part.ingredients.forEach(ing => ingredientsFormArray.push(this.createIngredientGroup(ing)));
  } else {
    ingredientsFormArray.push(this.createIngredientGroup()); // Default empty ingredient
  }

  // 2. Do the same for instructions array (FormControl array)
  const instructionsFormArray = this.fb.array<FormControl>([]);
  
  if (part?.instructions?.length) {
    part.instructions.forEach(step => 
      instructionsFormArray.push(this.fb.control(step, Validators.required) as FormControl)
    );
  } else {
    instructionsFormArray.push(this.fb.control('', Validators.required) as FormControl);
  }

  return this.fb.group({
    id: [part?.id || null],
    title: [part?.title || 'Main Assembly', Validators.required],
    ingredients: ingredientsFormArray,
    instructions: instructionsFormArray
  });
}

  addPart(): void {
    this.parts.push(this.createPartGroup());
  }

  removePart(index: number): void {
    if (this.parts.length > 1) {
      this.parts.removeAt(index);
    } else {
      this.snackBar.open('A recipe must have at least one part.', 'Close', { duration: 3000 });
    }
  }

  // --- Ingredient Builders & Actions ---
  createIngredientGroup(ing?: Ingredient): FormGroup {
    return this.fb.group({
      id: [ing?.id || null],
      name: [ing?.name || '', Validators.required],
      amount: [ing?.amount ?? 100, [Validators.required, Validators.min(0)]],
      unit: [ing?.unit || 'g', Validators.required],
      costPer100g: [ing?.costPer100g ?? null],
      caloriesPer100g: [ing?.caloriesPer100g ?? null]
    });
  }

  addIngredient(partIndex: number): void {
    this.getPartIngredients(partIndex).push(this.createIngredientGroup());
  }

  removeIngredient(partIndex: number, ingIndex: number): void {
    this.getPartIngredients(partIndex).removeAt(ingIndex);
  }

  // --- Instruction Step Actions ---
  addInstructionStep(partIndex: number): void {
    this.getPartInstructions(partIndex).push(this.fb.control('', Validators.required));
  }

  removeInstructionStep(partIndex: number, stepIndex: number): void {
    this.getPartInstructions(partIndex).removeAt(stepIndex);
  }

  // --- Load Existing Data (Edit Mode) ---
  private loadRecipeData(id: string): void {
    this.isLoading = true;
    this.recipeService.getRecipeById(id).subscribe({
      next: (recipe: Recipe | undefined) => {
        if (!recipe) {
      // Handle missing recipe (e.g., show error or redirect)
      return;
    }
        this.isLoading = false;
        this.recipeForm.patchValue({
          title: recipe.title,
          description: recipe.description,
          imageUrl: recipe.imageUrl,
          prepTimeMinutes: recipe.prepTimeMinutes,
          cookTimeMinutes: recipe.cookTimeMinutes,
          servings: recipe.servings,
          totalWeightGrams: recipe.totalWeightGrams,
          costPer100g: recipe.costPer100g,
          caloriesPer100g: recipe.caloriesPer100g
        });

        // Clear default parts and load existing
        this.parts.clear();
        recipe.parts.forEach(part => this.parts.push(this.createPartGroup(part)));
      },
      error: (err) => {
        this.isLoading = false;
        console.error('Failed to load recipe', err);
        this.snackBar.open('Could not load recipe details.', 'Close', { duration: 4000 });
      }
    });
  }

  // --- Submit Handler ---
  onSubmit(): void {
    if (this.recipeForm.invalid) {
      this.recipeForm.markAllAsTouched();
      this.snackBar.open('Please resolve form errors before submitting.', 'Dismiss', { duration: 4000 });
      return;
    }

    const payload = this.recipeForm.value;

    if (this.isEditMode && this.recipeId) {
      this.recipeService.updateRecipe(this.recipeId, payload).subscribe({
        next: () => {
          this.snackBar.open('Recipe updated successfully!', 'Close', { duration: 3000 });
          this.router.navigate(['/recipes', this.recipeId]);
        },
        error: (err) => {
          console.error('Update failed', err);
          this.snackBar.open('Failed to update recipe.', 'Close', { duration: 4000 });
        }
      });
    } else {
      this.recipeService.createRecipe(payload).subscribe({
        next: (created) => {
          this.snackBar.open('Recipe published successfully!', 'Close', { duration: 3000 });
          this.router.navigate(['/explore'])
     },
        error: (err) => {
          console.error('Creation failed', err);
          this.snackBar.open('Failed to create recipe.', 'Close', { duration: 4000 });
        }
      });
    }
  }



  fillMockData(): void {
  // 1. Basic Details
  this.recipeForm.patchValue({
    title: 'Japanese Tonkotsu Ramen',
    description: 'Rich, 12-hour pork bone broth served with springy ramen noodles, tender chashu pork belly, and soft-boiled marinated eggs.',
    imageUrl: 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624',
    prepTimeMinutes: 45,
    cookTimeMinutes: 180,
    servings: 4,
    totalWeightGrams: 1200,
    costPer100g: 2.15,
    caloriesPer100g: 185
  });

  // 2. Clear existing parts
  this.parts.clear();

  // Part 1: Chashu Pork Belly
  const part1 = this.createPartGroup({
    title: 'Chashu Pork Belly',
    ingredients: [
      { name: 'Pork Belly', amount: 800, unit: 'g' },
      { name: 'Soy Sauce', amount: 150, unit: 'ml' },
      { name: 'Sake', amount: 100, unit: 'ml' },
      { name: 'Mirin', amount: 100, unit: 'ml' },
      { name: 'Sugar', amount: 50, unit: 'g' },
      { name: 'Green Onion', amount: 3, unit: 'pcs' },
      { name: 'Ginger', amount: 30, unit: 'g' }
    ],
    instructions: [
      'Roll the pork belly tightly into a log and secure with butcher twine.',
      'Sear all sides in a hot pot until deeply browned.',
      'Add soy sauce, sake, mirin, sugar, scallions, and sliced ginger with enough water to submerge halfway.',
      'Cover and simmer on low for 2 hours until tender, turning occasionally.',
      'Slice thinly once cooled.'
    ]
  });

  // Part 2: Ramen Tare & Broth Base
  const part2 = this.createPartGroup({
    title: 'Broth & Shoyu Tare',
    ingredients: [
      { name: 'Pork Broth / Stock', amount: 1500, unit: 'ml' },
      { name: 'Reserved Chashu Braising Liquid', amount: 100, unit: 'ml' },
      { name: 'Dashi Powder', amount: 10, unit: 'g' },
      { name: 'Sesame Oil', amount: 15, unit: 'ml' }
    ],
    instructions: [
      'Strain the leftover chashu braising liquid to use as your shoyu tare base.',
      'Bring pork stock to a rolling boil and whisk in the dashi powder and sesame oil.'
    ]
  });

  // Part 3: Assembly & Toppings
  const part3 = this.createPartGroup({
    title: 'Assembly & Toppings',
    ingredients: [
      { name: 'Fresh Ramen Noodles', amount: 400, unit: 'g' },
      { name: 'Ramen Eggs (Ajitsuke Tamago)', amount: 4, unit: 'pcs' },
      { name: 'Nori Seaweed Sheets', amount: 4, unit: 'pcs' },
      { name: 'Menma (Bamboo Shoots)', amount: 100, unit: 'g' }
    ],
    instructions: [
      'Boil ramen noodles in salted water for 90 seconds until al dente, then drain.',
      'Ladle 2 tbsp of warm shoyu tare into each bowl and pour piping hot broth over it.',
      'Add drained noodles and arrange chashu slices, halved soft-boiled eggs, menma, and nori on top.',
      'Serve immediately.'
    ]
  });

  // Push parts into FormArray
  this.parts.push(part1);
  this.parts.push(part2);
  this.parts.push(part3);
}
}



